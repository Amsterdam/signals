"""
This module contains a minimal implementation of the StUF standard as it
applies to communication between the SIA system and Sigmax CityControl.
"""
import logging

from django.template.loader import render_to_string
from django.shortcuts import render
from lxml import etree
from rest_framework.response import Response
from rest_framework.views import APIView

from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend

logger = logging.getLogger(__name__)

ACTUALISEER_ZAAK_STATUS_SOAPACTION = \
    'http://www.egem.nl/StUF/sector/zkn/0310/UpdateZaak_Lk01'


def _parse_actualiseerZaakstatus_Lk01(xml):
    namespaces = {
        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
        'zaak': 'http://www.egem.nl/StUF/sector/zkn/0310',
        'stuf': 'http://www.egem.nl/StUF/StUF0301',
    }

    # strip the relevant information from the return message
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


def _handle_actualiseerZaakstatus_Lk01(request):
    """
    Checks that incoming message has required info, updates Signal if ok.
    """    
    # Check that the incoming message matches our expectations
    request_data = _parse_actualiseerZaakstatus_Lk01(request.body)
    zaak_uuid = request_data['zaak_uuid']

    # Retrieve the relevant Signal, error out if it cannot be found
    try:
        signals = Signal.objects.get(signal_id=request_data['zaak_uuid'])
    except Signal.DoesNotExist:
        return render(request, 'sigmax/actualiseerZaakstatus_Fo03.xml', {
            'error_msg': f'Melding met signal_id {zaak_uuid}',
            },
            content_type='text/xml'
        )

    # Generate status update data, then update the signal with the new status
    status_data = {
        'state': AFGEHANDELD_EXTERN,
        'text': 'AFGEHANDELD',
    }

    Signal.actions.update_status(status_data, signal)


# Not using CreateModelview here as it includes some functionality that is not needed.
# Through the CreateModelMixin and GenericAPIView (querysets, serializer class).

class CityControlReceiver(APIView):
    """
    Receive SOAP messages from CityControl and handle them.
    """
    authentication_classes = (JWTAuthBackend,)

    def post(self, request, format=None):
        """
        Dispatch 
        """
        if request.META['SOAPAction'] == ACTUALISEER_ZAAK_STATUS_SOAPACTION:
            return _handle_actualiseerZaakstatus_Lk01(request)
        else:
            log.debug()

        # emit Bv03 if ok
        # emit Fo03 if wrong 

# TODO:
# * dispatch on SOAPAction
# * find way of requiring message content
# * generate signal, send to sigmax, how do we test that the status is set to done? 
#   All this is asynchronous.
# * An endpoint that does nothing with incoming messages.
# * Full round trip test scenario.
