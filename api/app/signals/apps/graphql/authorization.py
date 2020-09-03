from functools import partial

import graphene
from django.contrib.gis.db import models
from graphene.types.utils import get_type
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import Field
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
    """
    Will first check if the permission classes are set and of the user has the correct set of
    permission. If the permission check does not raises a exception the parent 'validate'
    functionality is executed. The exception is catched by graphql and the message is shown.
    To implement create/update operation, subclass this class

    :param attrs:
    :return attrs:
    :raises Exception:
    """
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
    """
    Will first check if the permission classes are set and of the user has the correct set of
    permission. It overrides the mutate() methods to do permission checking. It also retrieves objects
    based on the model and id.
    The exception is catched by graphql and the message is shown. To implement a delete operation,
    subclass this class.


    :param attrs:
    :return attrs:
    :raises Exception:
    """
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
        if not model or not issubclass(model, models.Model):
            raise Exception("empty or invalid model")
        cls.model = model
        cls.permission_classes = permission_classes

    class Arguments:
        id = graphene.Int()

    ok = graphene.Boolean()

    @classmethod
    def get_queryset(cls):
        # DRF depends on get_queryset().model, self has .model property
        return cls

    @classmethod
    def mutate(cls, root, info, id):
        _check_permissions(cls.permission_classes, info.context, cls)
        obj = cls.model.objects.get(id=id)
        obj.delete()
        return cls(ok=True)


class SiaAuthNodeField(Field):
    def __init__(self, node, type=False, deprecation_reason=None, name=None, **kwargs):
        assert issubclass(node, SiaAuthNode), 'NodeField can only operate in SiaAuthNodeField'
        self.node_type = node
        self.field_type = type

        super(SiaAuthNodeField, self).__init__(
            # If we don's specify a type, the field type will be the node interface
            type or node,
            id=graphene.Int(required=True))

    def get_resolver(self, parent_resolver):
        return partial(self.node_type.node_resolver, get_type(self.field_type))


class SiaAuthNode(graphene.relay.Node):
    """
    Will first check if the permission classes are set and of the user has the correct set of
    permission. It overrides the node_resolver() methods to do permission checking and invokes the
    parent afterwards. It also retrieves objects based on the model and id. The exception is catched
    by graphql and the message is shown. To implement a single node operation, subclass this class.


    :param attrs:
    :return attrs:
    :raises Exception:
    """

    model = None
    permission_classes = None

    class Meta:
        name = 'CNode'

    @classmethod
    def Field(cls, *args, **kwargs):  # noqa: N802
        # retrieve model from DjangoObjectType
        for arg in args:
            if hasattr(arg._meta, 'model') and not cls.model:
                cls.model = arg._meta.model
            if hasattr(arg, 'permission_classes') and not cls.permission_classes:
                cls.permission_classes = arg.permission_classes

        if not cls.model or not issubclass(cls.model, models.Model):
            raise Exception("empty or invalid model")
        return SiaAuthNodeField(cls, *args, **kwargs)

    @classmethod
    def get_queryset(cls):
        # DRF depends on get_queryset().model, cls has .model property
        return cls

    @classmethod
    def node_resolver(cls, only_type, root, info, id):
        _check_permissions(cls.permission_classes, info.context, cls)
        return info.return_type.graphene_type._meta.model.objects.get(id=id)


class SiaAuthConnectionField(DjangoFilterConnectionField):
    """
    Will first check if the permission classes are set and of the user has the correct set of
    permission. It overrides the resolve_queryset() methods to do permission checking and invokes the
    parent afterwards. The exception is catched by graphql and the message is shown. To implement
    a filtered nodes operation, subclass this class.


    :param attrs:
    :return attrs:
    :raises Exception:
    """
    model = None
    permission_classes = None

    def __init__(self, type, *args, **kwargs):
        super(SiaAuthConnectionField, self).__init__(
            type=type,
            *args,
            **kwargs
        )
        if hasattr(type._meta, 'model'):
            self.model = type._meta.model
        if not self.model or not issubclass(self.model, models.Model):
            raise Exception("empty or invalid model")
        self.permission_classes = type.permission_classes

    def resolve_queryset(
        self, connection, iterable, info, args, filtering_args, filterset_class
    ):
        _check_permissions(self.permission_classes, info.context, self)
        return super(SiaAuthConnectionField, self).resolve_queryset(
            connection, iterable, info, args, filtering_args, filterset_class
        )

    def get_queryset(self):
        # DRF depends on get_queryset().model, self has .model property
        return self
