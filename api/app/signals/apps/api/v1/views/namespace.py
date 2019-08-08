from rest_framework.response import Response
from rest_framework.views import APIView


class NamespaceView(APIView):
    """
    Used for the curies namespace, at this moment it is just a dummy landing page so that we have
    a valid URI that resolves

    TODO: Implement HAL standard for curies in the future
    """

    def get(self, request):
        return Response()
