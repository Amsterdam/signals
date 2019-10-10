from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_412_PRECONDITION_FAILED, HTTP_501_NOT_IMPLEMENTED


class PreconditionFailed(APIException):
    status_code = HTTP_412_PRECONDITION_FAILED
    default_detail = _('Precondition failed.')
    default_code = 'precondition_failed'


class NotImplementedException(APIException):
    status_code = HTTP_501_NOT_IMPLEMENTED
    default_detail = 'Not implemented'
