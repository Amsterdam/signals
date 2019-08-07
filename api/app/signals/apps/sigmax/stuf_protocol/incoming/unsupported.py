"""
Send StUF protocol error message on reception of unsupported SOAP actions.
"""

import logging

from django.shortcuts import render

logger = logging.getLogger(__name__)


def handle_unsupported_soap_action(request):
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
        status=500
    )
