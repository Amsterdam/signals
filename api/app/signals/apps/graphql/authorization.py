import graphene
from django.contrib.gis.db import models
from rest_framework import serializers

from signals.apps.api.generics.permissions import ModelWritePermissions, SIAPermissions


def _check_permissions(permission_classes, request, view):
    if not permission_classes:
        return

    for permission_class in permission_classes:
        permission = permission_class()

        if not permission.has_permission(request=request, view=view):
            raise Exception(getattr(permission, 'message', None))


class MutationPermissionSerializer(serializers.ModelSerializer):
    permission_classes = None

    @classmethod
    def __init_subclass__(
        cls,
        permission_classes=(SIAPermissions & ModelWritePermissions,),
        **kwargs
    ):
        super().__init_subclass__(**kwargs)
        cls.permission_classes = permission_classes

    def get_queryset(self):
        # DRF depends on get_queryset().model, self.Meta has .model property
        return self.Meta

    def check_permissions(self):
        if not self.permission_classes:
            return

        # inject self as view, in order to get the model
        request = self.context.get('request')
        view = self.context.get('view', None) or self
        _check_permissions(self.permission_classes, request, view)

    def validate(self, attrs):
        self.check_permissions()
        return super().validate(attrs=attrs)


class DeleteModelMutation(graphene.Mutation):
    model = None
    permission_classes = None

    @classmethod
    def __init_subclass__(
        cls,
        model=model,
        permission_classes=(SIAPermissions & ModelWritePermissions,),
        **kwargs
    ):
        super().__init_subclass__(**kwargs)
        if not model or not isinstance(model, type(models.Model)):
            raise Exception("empty or invalid model")
        cls.model = model
        cls.permission_classes = permission_classes

    class Arguments:
        id = graphene.Int()

    ok = graphene.Boolean()

    @classmethod
    def get_queryset(cls):
        # DRF depends on get_queryset().model, self.Meta has .model property
        return cls

    @classmethod
    def mutate(cls, root, info, id):
        _check_permissions(cls.permission_classes, info.context, cls)
        obj = cls.model.objects.get(id=id)
        obj.delete()
        return cls(ok=True)
