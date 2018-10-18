import re

from django.http import JsonResponse
from rest_framework.views import APIView

from signals.auth.backend import JWTAuthBackend


class UserMeView(APIView):
    """Handle information about user me."""
    authentication_classes = (JWTAuthBackend, )

    def get(self, request):
        data = {}
        user = request.user
        if user:
            data['username'] = user.username
            data['email'] = user.email
            data['is_staff'] = user.is_staff is True
            data['is_superuser'] = user.is_superuser is True
            groups = []
            departments = []
            for g in request.user.groups.all():
                match = re.match(r"^dep_(\w+)$", g.name)
                if match:
                    departments.append(match.group(1))
                else:
                    groups.append(g.name)
            data['groups'] = groups
            data['departments'] = departments
            data['permissions'] = [p for p in user.get_all_permissions() if p.startswith('signals')]
        return JsonResponse(data)
