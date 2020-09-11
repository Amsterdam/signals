import functools


def enforce_request_version_v1(func):
    """
    Makes sure the request is always on version V1
    TODO: Remove this decorator and its implementation when V0 is removed from the codebase
    """
    @functools.wraps(func)
    def function_wrapper(self, *args, **kwargs):
        original_version = self.context['request'].version
        self.context['request'].version = 'v1'

        result = func(self, *args, **kwargs)

        self.context['request'].version = original_version
        return result
    return function_wrapper
