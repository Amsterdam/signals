from change_log.logger import ChangeLogger


class ChangeLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ChangeLogger.thread.request = request
        response = self.get_response(request)
        return response
