from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend
from signals.apps.relations.models import Relation
from signals.apps.relations.rest_framework.serializers import RelatedSignalSerializer


class SignalRelatedViewSet(ModelViewSet):
    queryset = Relation.objects.all()

    authentication_classes = [JWTAuthBackend]
    permission_classes = (SIAPermissions,)

    serializer_class = RelatedSignalSerializer

    # We only allow these methods
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']

    def get_queryset(self, *args, **kwargs):
        return Signal.objects.filter_for_user(user=self.request.user)

    def list(self, request, *args, **kwargs):
        source_signal = self.get_object()

        serializer = self.get_serializer(self.get_queryset().filter(
            pk__in=[relation.target.pk for relation in Relation.objects.filter(source=source_signal)]
        ), many=True)

        return Response(serializer.data)

    def link(self, request, *args, **kwargs):
        source_signal = self.get_object()
        target_signal = self.get_queryset().get(pk=request.data['id'])

        if not target_signal or source_signal == target_signal:
            return HttpResponse(status=400)

        Relation.objects.get_or_create(source=source_signal, target=target_signal)
        Relation.objects.get_or_create(source=target_signal, target=source_signal)

        return self.list(request)

    def unlink(self, request, *args, **kwargs):
        source_signal = self.get_object()
        target_signal = self.get_queryset().get(pk=request.data['id'])

        if not target_signal or source_signal == target_signal:
            return HttpResponse(status=400)

        Relation.objects.filter(source=source_signal, target=target_signal).delete()
        Relation.objects.filter(source=target_signal, target=source_signal).delete()

        return self.list(request)
