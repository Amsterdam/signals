from django.conf import settings


def admin_feature_flags(request):
    return {'FEATURE_FLAGS': settings.FEATURE_FLAGS}
