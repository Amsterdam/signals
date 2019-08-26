from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_504_GATEWAY_TIMEOUT


class GateWayTimeout(APIException):
    status_code = HTTP_504_GATEWAY_TIMEOUT
