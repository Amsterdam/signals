from django.conf import settings


def settings_in_context(request):
    return {
        'FEATURE_FLAGS': settings.FEATURE_FLAGS,
        'ORGANIZATION_NAME': settings.ORGANIZATION_NAME,
    }
