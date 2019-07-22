"""
This module contains a minimal implementation of the StUF standard as it
applies to communication between the SIA system and Sigmax CityControl.
"""
import logging
import re

from django.core.exceptions import ValidationError
from django.shortcuts import render
from lxml import etree
from rest_framework.views import APIView

from signals.apps.signals import workflow
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend

logger = logging.getLogger(__name__)

# Note the quotes in SOAPAction header are required by SOAP
ACTUALISEER_ZAAK_STATUS_SOAPACTION = \
    '"http://www.egem.nl/StUF/sector/zkn/0310/actualiseerZaakstatus_Lk01"'


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


def _handle_unknown_soap_action(request):
    """
    Requests with unknown/unsupported SOAPActions are handled here
    """
    # TODO: nicer Fo03 message template (this is not for actualiseerZaakstatus ..
    error_msg = 'SOAPAction: {} is not supported'.format(request.META['HTTP_SOAPACTION'])
    logger.warning(error_msg, stack_info=True)
    return render(
        request,
        'sigmax/actualiseerZaakstatus_Fo03.xml',
        context={'error_msg': error_msg, },
        content_type='text/xml; charset=utf-8',
        status=500)


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


def _handle_actualiseerZaakstatus_Lk01(request):  # noqa: C901
    """
    Checks that incoming message has required info, updates Signal if ok.
    """
    # Note: `sequence_number` below is not currently checked against outstanding
    # meldingen (Signal instances) sent to CityControl. This is safe because the
    # sequence numbers are only relevant in the CityControl software (and we
    # reply using exactly the sequence number provided by CityControl).

    request_data = _parse_actualiseerZaakstatus_Lk01(request.body)
    zaak_id = request_data['zaak_id']  # zaak identifier in CityControl

    # Retrieve the relevant Signal, error out if it cannot be found or incoming
    # zaak identificatie cannot be parsed.
    try:
        _id, sequence_number = _parse_zaak_identificatie(zaak_id)
        signal = Signal.objects.get(pk=_id)
    except Signal.DoesNotExist:
        error_msg = f'Melding met sia_id {zaak_id} niet gevonden.'
        logger.warning(error_msg, exc_info=True)
        return render(
            request,
            'sigmax/actualiseerZaakstatus_Fo03.xml',
            context={'error_msg': error_msg, },
            content_type='text/xml; charset=utf-8',
            status=500)
    except ValueError as e:
        error_msg = str(e)
        logger.warning(error_msg, exc_info=True)
        return render(
            request,
            'sigmax/actualiseerZaakstatus_Fo03.xml',
            context={'error_msg': error_msg, },
            content_type='text/xml; charset=utf-8',
            status=500)

    # update Signal status upon receiving message
    default_text = 'Melding is afgehandeld door THOR.'

    # We strip whitespace
    if request_data['resultaat'].strip() and request_data['reden'].strip():
        status_text = '{}: {}'.format(
            request_data['resultaat'].strip(),
            request_data['reden'].strip()
        )
    elif request_data['resultaat'].strip():  # only resultaat
        status_text = '{}: Geen reden aangeleverd vanuit THOR'.format(
            request_data['resultaat'].strip()
        )
    elif request_data['reden'].strip():
        status_text = 'Geen resultaat aangeleverd vanuit THOR: {}'.format(
            request_data['reden']
        )
    else:
        status_text = default_text

    status_data = {
        'state': workflow.AFGEHANDELD_EXTERN,
        'text': status_text,
        'extra_properties': {
            'sigmax_datum_afgehandeld': request_data['datum_afgehandeld'],
            'sigmax_resultaat': request_data['resultaat'],
            'sigmax_reden': request_data['reden'],
        }
    }

    try:
        Signal.actions.update_status(data=status_data, signal=signal)
    except ValidationError:
        error_msg = f'Melding met zaak identificatie {zaak_id} en volgnummer {sequence_number} was niet in verzonden staat in SIA.'  # noqa
        logger.warning(error_msg, exc_info=True)
        return render(
            request,
            'sigmax/actualiseerZaakstatus_Fo03.xml',
            context={'error_msg': error_msg, },
            content_type='text/xml; charset=utf-8',
            status=500)

    bv03_context = {'signal': signal}
    if sequence_number is not None:
        bv03_context['sequence_number'] = '{0:02d}'.format(sequence_number)

    response = render(
        request,
        'sigmax/actualiseerZaakstatus_Bv03.xml',
        context=bv03_context,
        content_type='text/xml; charset=utf-8', status=200
    )

    logging.warning('SIA sent the following Bv03 message:', extra={
        'content': response.content.decode('utf-8')
    }, stack_info=True)
    return response
