"""
This module contains a minimal implementation of the StUF standard as it
applies to communication between the SIA system and Sigmax CityControl.
"""
import logging

from django.shortcuts import render
from rest_framework.views import APIView

from signals.apps.sigmax.stuf_protocol.incoming import (
    ACTUALISEER_ZAAK_STATUS,
    handle_actualiseerZaakstatus_Lk01,
    handle_unsupported_soap_action
)
from signals.auth.backend import JWTAuthBackend

logger = logging.getLogger(__name__)


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

        if request.META['HTTP_SOAPACTION'] == ACTUALISEER_ZAAK_STATUS:
            return handle_actualiseerZaakstatus_Lk01(request)
        else:
            return handle_unsupported_soap_action(request)
