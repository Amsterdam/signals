"""
Support for creeerZaak_Lk01 messages to send to CityControl.
"""
import logging
import os
from datetime import timedelta

from django.template.loader import render_to_string

from signals.apps.sigmax.stuf_protocol.outgoing.stuf import _send_stuf_message
from signals.apps.signals.models import (
    STADSDEEL_CENTRUM,
    STADSDEEL_NIEUWWEST,
    STADSDEEL_NOORD,
    STADSDEEL_OOST,
    STADSDEEL_WEST,
    STADSDEEL_WESTPOORT,
    STADSDEEL_ZUID,
    STADSDEEL_ZUIDOOST,
    Priority
)

logger = logging.getLogger(__name__)


CREEER_ZAAK = '"http://www.egem.nl/StUF/sector/zkn/0310/CreeerZaak_Lk01"'

SIGNALS_API_BASE = os.getenv('SIGNALS_API_BASE',
                             'https://acc.api.data.amsterdam.nl')

SIGMAX_REQUIRED_ADDRESS_FIELDS = ['woonplaats', 'openbare_ruimte', 'huisnummer']
# See ticket SIG-743 for the origin of this mapping:
SIGMAX_STADSDEEL_MAPPING = {
    STADSDEEL_CENTRUM: 'SDC',
    STADSDEEL_NOORD: 'SDN',
    STADSDEEL_NIEUWWEST: 'SDNW',
    STADSDEEL_OOST: 'SDO',
    STADSDEEL_WEST: 'SDW',
    STADSDEEL_ZUID: 'SDZ',
    STADSDEEL_ZUIDOOST: 'SDZO',
    STADSDEEL_WESTPOORT: 'SDWP',  # not part of spec, but present in our data model
}


def _generate_omschrijving(signal, seq_no):
    """Generate brief descriptive text for list view in CityControl"""
    # Note: we do not mention main or category here (too many characters)
    is_urgent = 'URGENT' if signal.priority.priority == Priority.PRIORITY_HIGH else 'Terugkerend'

    # Borough (stadsdeel) codes for Sigmax/CityControl are custom and do not
    # match the official ones as used by the municipality of Amsterdam; hence:
    stadsdeel = signal.location.stadsdeel
    stadsdeel_code_sigmax = SIGMAX_STADSDEEL_MAPPING.get(stadsdeel, 'SD--')

    return 'SIA-{}.{} {} {} {}'.format(
        signal.id,
        seq_no,
        is_urgent,
        stadsdeel_code_sigmax,
        signal.location.short_address_text,
    )


def _address_matches_sigmax_expectation(address_dict):
    """Return whether an address has all information Sigmax/CityControl needs.

    Note: we do not validate the address against the Basisadministratie
    Adresses en Gebouwen (BAG). We do check that all required components are
    non-empty.
    """
    # TODO: consider checking the existence of an address / make it impossible
    # for non (BAG) validated addresses to reach Sigmax.
    # TODO: consider moving to a JSONSchema style check here (more concise)
    if not address_dict:  # protect against empty address fields
        return False

    for field in SIGMAX_REQUIRED_ADDRESS_FIELDS:
        if field not in address_dict:
            return False

    # We want a "huisnummer" to be (convertable to) an actual number
    try:
        int(address_dict['huisnummer'])
    except (ValueError, TypeError):
        return False

    # We want non-empty strings for "woonplaats" and "openbare_ruimte"
    if (not isinstance(address_dict['woonplaats'], str) or
            not isinstance(address_dict['openbare_ruimte'], str)):
        return False

    if (not address_dict['woonplaats'].strip() or
            not address_dict['openbare_ruimte'].strip()):
        return False

    return True


def _generate_creeerZaak_Lk01(signal, seq_no):
    """Generate XML for Sigmax creeerZaak_Lk01

    SIGMAX will be set up to receive Signals (meldingen) that have no address but do have
    coordinates (middle of park, somewhere on a body of water, etc.).
    """
    num_days_priority_mapping = {
        Priority.PRIORITY_HIGH: 1,
        Priority.PRIORITY_NORMAL: 3,
    }
    incident_date_end = (
        signal.created_at + timedelta(days=num_days_priority_mapping[signal.priority.priority]))

    return render_to_string('sigmax/creeerZaak_Lk01.xml', context={
        'address_matches_sigmax_expectation':
            _address_matches_sigmax_expectation(signal.location.address),
        'signal': signal,
        'sequence_number': seq_no,
        'incident_date_end': signal.incident_date_end or incident_date_end,
        'x': str(signal.location.geometrie.x),
        'y': str(signal.location.geometrie.y),
        'omschrijving': _generate_omschrijving(signal, seq_no),
    })


def send_creeerZaak_Lk01(signal, seq_no):
    soap_action = CREEER_ZAAK
    msg = _generate_creeerZaak_Lk01(signal, seq_no)
    response = _send_stuf_message(msg, soap_action)

    logger.info('Sent %s', soap_action)
    logger.info('Received:\n%s', response.text)
    return response
