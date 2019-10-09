from django.http import JsonResponse
from django.utils import timezone
from rest_framework.views import APIView

from signals.auth.backend import JWTAuthBackend


class PingView(APIView):
    """
    Only for first setup of the users/roles/permission API
    Will be deleted in future commits
    """
    authentication_classes = (JWTAuthBackend, )

    def get(self, request):
        return JsonResponse({'now': timezone.now()})
