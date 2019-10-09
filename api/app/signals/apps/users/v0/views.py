import re

from django.http import JsonResponse
from rest_framework.views import APIView

from signals.auth.backend import JWTAuthBackend


class UserMeView(APIView):
    """Handle information about user me."""
    authentication_classes = (JWTAuthBackend, )

    def get(self, request):
        data = {
            'username': request.user.username,
            'email': request.user.email,
            'is_staff': request.user.is_staff is True,
            'is_superuser': request.user.is_superuser is True,
            'permissions': [
                permission
                for permission in request.user.get_all_permissions()
                if permission.startswith('signals')
            ],
        }

        groups = []
        departments = []
        for group in request.user.groups.all():
            match = re.match(r"^dep_(\w+)$", group.name)
            if match:
                departments.append(match.group(1))
            else:
                groups.append(group.name)
        data['groups'] = groups
        data['departments'] = departments

        return JsonResponse(data)
