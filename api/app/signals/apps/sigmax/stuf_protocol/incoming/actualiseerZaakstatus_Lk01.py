"""
Support for actualiseerZaakstatus_Lk01 messages from CityControl.
"""

import logging
import re

from django.core.exceptions import ValidationError
from django.shortcuts import render
from lxml import etree

from signals.apps.sigmax.models import CityControlRoundtrip
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal

logger = logging.getLogger(__name__)

ACTUALISEER_ZAAK_STATUS = '"http://www.egem.nl/StUF/sector/zkn/0310/actualiseerZaakstatus_Lk01"'


def _parse_actualiseerZaakstatus_Lk01(xml):
    namespaces = {
        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
        'zaak': 'http://www.egem.nl/StUF/sector/zkn/0310',
        'stuf': 'http://www.egem.nl/StUF/StUF0301',
    }

    # strip the relevant information from the return message
    assert type(xml) == type(b'a')  # noqa: E721
    tree = etree.fromstring(xml)

    def xpath(expression):
        found = tree.xpath(expression, namespaces=namespaces)
        out = found[0].text if found and found[0].text else ''
        assert isinstance(out, str)
        return out

    # TODO: handle missing data / nice error reporting
    zaak_id = xpath('//zaak:object/zaak:identificatie')
    resultaat_omschrijving = xpath('//zaak:object/zaak:resultaat/zaak:omschrijving')
    datum_status_gezet = xpath('//zaak:object/zaak:heeft/zaak:datumStatusGezet')
    einddatum = xpath('//zaak:object/zaak:einddatum')
    reden = xpath('//zaak:object/zaak:resultaat/zaak:toelichting')

    return {
        'zaak_id': zaak_id.strip(),
        'datum_afgehandeld': datum_status_gezet or einddatum,
        'resultaat': resultaat_omschrijving,
        'reden': reden,
    }


def _parse_zaak_identificatie(zaak_id):
    """Parse incoming zaakidentificatie (find SIA id and sequence number)."""
    old_style_pattern = re.compile(r'^\s*SIA-(?P<_id>[1-9]\d*)\s*$')
    new_style_pattern = re.compile(r'^\s*SIA-(?P<_id>[1-9]\d*)\.(?P<sequence_number>\d{2})\s*$')

    if zaak_id is None:
        raise ValueError("Incorrect value for sia_id: {}".format(repr(zaak_id)))

    m = old_style_pattern.match(zaak_id)
    if m:
        d = m.groupdict()
        return int(d['_id']), None

    m = new_style_pattern.match(zaak_id)
    if m:
        d = m.groupdict()
        _id = int(d['_id'])
        sequence_number = int(d['sequence_number'])

        if sequence_number == 0:  # Cannot have 0 as sequence_number
            raise ValueError("Incorrect value for sia_id: {}".format(repr(zaak_id)))

        return _id, sequence_number

    else:
        raise ValueError("Incorrect value for sia_id: {}".format(repr(zaak_id)))


def _get_status_text_actualiseerZaakstatus_Lk01(request_data):
    """
    Upon reception of new "zaak" status, derive SIA Signal status update text.
    """
    resultaat_text = request_data.get('resultaat', '').strip()
    resultaat_text = resultaat_text if resultaat_text else 'Geen resultaat aangeleverd vanuit THOR'
    reden_text = request_data.get('reden', '').strip()
    reden_text = reden_text if reden_text else 'Geen reden aangeleverd vanuit THOR'
    default_text = 'Melding is afgehandeld door THOR.'

    if not resultaat_text and not default_text:
        return default_text
    else:
        return '{}: {}'.format(resultaat_text, reden_text)


def _update_status_actualiseerZaakstatus_Lk01(signal, request_data):
    """
    Upon reception of a new "zaak" status, we update the Signal status.

    Note: this is the happy flow, only happens when the Signal was in the
    expected state in SIA --- else see _add_note_actualiseerZaakstatus_Lk01.
    """
    status_text = _get_status_text_actualiseerZaakstatus_Lk01(request_data)
    status_data = {
        'state': workflow.AFGEHANDELD_EXTERN,
        'text': status_text,
        'extra_properties': {
            'sigmax_datum_afgehandeld': request_data['datum_afgehandeld'],
            'sigmax_resultaat': request_data['resultaat'],
            'sigmax_reden': request_data['reden'],
        }
    }

    # We let exceptions bubble up (must lead to a error message to CityControl).
    Signal.actions.update_status(data=status_data, signal=signal)


def _add_note_actualiseerZaakstatus_Lk01(signal, request_data):
    """
    Upon reception of a new "zaak" status, we add a note to that effect.

    Note: this is the fallback flow, happens when a Signal is not in the
    expected status within SIA.
    """
    status_text = _get_status_text_actualiseerZaakstatus_Lk01(request_data)

    note_text = f'Zaak status update ontvangen van CityControl terwijl SIA melding niet in verzonden staat was.\n\n {status_text}' # noqa
    note_data = {'text': note_text}

    Signal.actions.create_note(note_data, signal)


def _get_actualiseerZaakstatus_Bv03(request, bv03_context):
    return render(
        request,
        'sigmax/actualiseerZaakstatus_Bv03.xml',
        context=bv03_context,
        content_type='text/xml; charset=utf-8', status=200
    )


def _get_actualiseerZaakstatus_Fo03(request, error_msg):
    return render(
        request,
        'sigmax/actualiseerZaakstatus_Fo03.xml',
        context={'error_msg': error_msg, },
        content_type='text/xml; charset=utf-8',
        status=500
    )


def _increment_roundtrip_count(signal, sequence_number):
    """
    Increment the round trip count to at least the received sequence number.

    Note:
    - we do not want to re-use sequence numbers
    """
    if sequence_number is None:
        return  # old style zaak identificatie, skip

    n_trips = CityControlRoundtrip.objects.filter(_signal=signal).count()
    delta = sequence_number - n_trips

    if delta > 0:
        # Case where one or more "zaak" objects were created in CityControl
        # without it being known to SIA (happens when Bv03 messages upon
        # creation were not received by SIA, or not sent by CityControl ---
        # a problem that was observed in our logs).
        # We want to avoid re-using "zaak identificatie" (and thus sequence
        # numbers).
        round_trips = [CityControlRoundtrip(_signal=signal) for i in range(delta)]
        CityControlRoundtrip.bulk_create(round_trips)
    elif delta < 0:
        # Possible when receiving an updates to Signals out of order. Which may
        # become possible in the future (if we relax the rules around sending)
        # "zaak" objects to CityControl. TBD
        pass
    else:
        # sequence number as expected, no action required
        pass


def handle_actualiseerZaakstatus_Lk01(request):  # noqa: C901
    """
    Checks that incoming message has required info, updates Signal if ok.
    """
    # Note: `sequence_number` below is not currently checked against outstanding
    # meldingen (Signal instances) sent to CityControl. This is safe because the
    # sequence numbers are only relevant in the CityControl software (and we
    # reply using exactly the sequence number provided by CityControl).

    request_data = _parse_actualiseerZaakstatus_Lk01(request.body)
    zaak_id = request_data['zaak_id']  # zaak identifier in CityControl

    # Retrieve the relevant Signal, reply to CityControl with a
    # actualiseerZaakstatus_Fo03 message.
    try:
        _id, sequence_number = _parse_zaak_identificatie(zaak_id)
        signal = Signal.objects.get(pk=_id)
    except Signal.DoesNotExist:
        error_msg = f'Melding met sia_id {zaak_id} niet gevonden.'
        logger.warning(error_msg, exc_info=True)
        return _get_actualiseerZaakstatus_Fo03(request, error_msg)
    except ValueError as e:
        error_msg = str(e)
        logger.warning(error_msg, exc_info=True)
        return _get_actualiseerZaakstatus_Fo03(request, error_msg)

    # Update status according to workflow or add a note to the Signal
    # that an update was received but not expected.
    try:
        _update_status_actualiseerZaakstatus_Lk01(signal, request_data)
    except ValidationError:
        error_msg = f'Melding met zaak identificatie {zaak_id} en volgnummer {sequence_number} was niet in verzonden staat in SIA.'  # noqa
        logger.warning(error_msg, exc_info=True)

        _add_note_actualiseerZaakstatus_Lk01(signal, request_data)
        _increment_roundtrip_count(signal, sequence_number)
        return _get_actualiseerZaakstatus_Fo03(request, error_msg)

    # Happy flow, send a actualiseerZaakstatus_Bv03 to CityControl to confirm
    # that the update was received and stored in SIA.
    bv03_context = {'signal': signal}
    if sequence_number is not None:
        bv03_context['sequence_number'] = '{0:02d}'.format(sequence_number)

    response = _get_actualiseerZaakstatus_Bv03(request, bv03_context)

    logging.warning('SIA sent the following Bv03 message:', extra={
        'content': response.content.decode('utf-8')
    }, stack_info=True)
    return response
