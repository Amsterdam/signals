from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from signals.apps.api.generics import mixins
from signals.apps.api.generics.permissions import ModelWritePermissions, SIAPermissions
from signals.apps.api.v1.serializers import StateStatusMessageTemplateSerializer
from signals.apps.signals.models import Category, StatusMessageTemplate
from signals.auth.backend import JWTAuthBackend


class StatusMessageTemplatesViewSet(mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                                    viewsets.GenericViewSet):
    serializer_class = StateStatusMessageTemplateSerializer

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions & ModelWritePermissions,)
    pagination_class = None

    queryset = StatusMessageTemplate.objects.none()

    def get_object(self):
        if 'slug' in self.kwargs and 'sub_slug' in self.kwargs:
            kwargs = {'parent__slug': self.kwargs['slug'],
                      'slug': self.kwargs['sub_slug']}
        else:
            kwargs = {'slug': self.kwargs['slug']}

        obj = get_object_or_404(Category.objects.all(), **kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_serializer_context(self):
        context = super(StatusMessageTemplatesViewSet, self).get_serializer_context()
        context.update({'category': self.get_object()})
        return context

    def retrieve(self, request, *args, **kwargs):
        status_message_templates = self.get_object().status_message_templates.all()
        serializer = self.get_serializer(status_message_templates, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return self.retrieve(request, *args, **kwargs)
