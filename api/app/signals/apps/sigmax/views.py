"""
This module contains a minimal implementation of the StUF standard as it
applies to communication between the SIA system and Sigmax CityControl.
"""
import logging

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
    assert type(xml) != type(b'a')  # noqa: E721
    tree = etree.fromstring(xml)

    def xpath(expression):
        found = tree.xpath(expression, namespaces=namespaces)
        return found[0].text if found else ''

    # TODO: handle missing data / nice error reporting
    zaak_uuid = xpath('//zaak:stuurgegevens/stuf:referentienummer')
    resultaat_omschrijving = xpath('//zaak:object/zaak:resultaat/zaak:omschrijving')
    datum_status_gezet = xpath('//zaak:object/zaak:heeft/zaak:datumStatusGezet')
    einddatum = xpath('//zaak:object/zaak:einddatum')
    reden = xpath('//zaak:object/zaak:resultaat/zaak:toelichting')

    return {
        'zaak_uuid': zaak_uuid,
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


def _handle_actualiseerZaakstatus_Lk01(request):
    """
    Checks that incoming message has required info, updates Signal if ok.
    """
    # TODO: Check that the incoming message matches our expectations, else Fo03

    request_data = _parse_actualiseerZaakstatus_Lk01(request.body.decode('utf-8', 'strict'))
    zaak_uuid = request_data['zaak_uuid']

    # Retrieve the relevant Signal, error out if it cannot be found
    try:
        signal = Signal.objects.get(signal_id=request_data['zaak_uuid'])
    except Signal.DoesNotExist:
        error_msg = f'Melding met signal_id {zaak_uuid} niet gevonden.'
        logger.warning(error_msg, exc_info=True)
        return render(
            request,
            'sigmax/actualiseerZaakstatus_Fo03.xml',
            context={'error_msg': error_msg, },
            content_type='text/xml; charset=utf-8',
            status=500)

    # update Signal status upon receiving message
    status_data = {
        'state': workflow.AFGEHANDELD_EXTERN,
        'text': 'Afgehandeld door via SIGMAX / CITYCONTROL',
    }

    try:
        Signal.actions.update_status(data=status_data, signal=signal)
    except ValidationError:
        error_msg = f'Melding met signal_id {zaak_uuid} was niet in verzonden staat'
        logger.warning(error_msg, exc_info=True)
        return render(
            request,
            'sigmax/actualiseerZaakstatus_Fo03.xml',
            context={'error_msg': error_msg, },
            content_type='text/xml; charset=utf-8',
            status=500)

    return render(request, 'sigmax/actualiseerZaakstatus_Bv03.xml', context={
        'zaak_uuid': signal.signal_id
    }, content_type='text/xml; charset=utf-8', status=200)


class CityControlReceiver(APIView):
    """
    Receive SOAP messages from CityControl and handle them.
    """
    authentication_classes = (JWTAuthBackend,)

    def post(self, request, format=None):
        """
        Handle SOAP requests, dispatch on SOAPAction header.
        """
        # https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383528
        if 'HTTP_SOAPACTION' not in request.META:
            error_msg = 'SOAPAction header not set'
            logger.warning(error_msg, stack_info=True)
            return render(
                request,
                'sigmax/actualiseerZaakstatus_Fo03.xml',
                context={'error_msg': error_msg, },
                content_type='text/xml; charset=utf-8',
                status=500)

        if request.META['HTTP_SOAPACTION'] == ACTUALISEER_ZAAK_STATUS_SOAPACTION:
            return _handle_actualiseerZaakstatus_Lk01(request)
        else:
            return _handle_unknown_soap_action(request)
