from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType

from signals.apps.graphql.filters import (
    CategoryFilterSet,
    DepartmentFilterSet,
    ServiceLevelObjectiveFilterSet,
    StatusMessageTemplateFilterSet
)
from signals.apps.signals.models import (
    Category,
    Department,
    ServiceLevelObjective,
    StatusMessageTemplate
)


class DepartmentType(DjangoObjectType):
    class Meta:
        description = 'Representation of a Department'
        model = Department
        fields = (
            'code',
            'name',
            'is_intern',
        )
        filterset_class = DepartmentFilterSet
        interfaces = (relay.Node,)


class ServiceLevelObjectiveType(DjangoObjectType):
    class Meta:
        description = 'Representation of a ServiceLevelObjective'
        model = ServiceLevelObjective
        fields = (
            'n_days',
            'use_calendar_days',
            'created_at',
        )
        filterset_class = ServiceLevelObjectiveFilterSet
        interfaces = (relay.Node,)


class StatusMessageTemplateType(DjangoObjectType):
    class Meta:
        description = 'Representation of a StatusMessageTemplate'
        model = StatusMessageTemplate
        fields = (
            'title',
            'text',
            'state',
        )
        filterset_class = StatusMessageTemplateFilterSet
        interfaces = (relay.Node,)


class CategoryType(DjangoObjectType):
    departments = DjangoFilterConnectionField(DepartmentType, filterset_class=DepartmentFilterSet)

    class Meta:
        description = 'Representation of a Category'
        model = Category
        fields = (
            'parent',
            'name',
            'slug',
            'description',
            'handling_message',
            'is_active',
            'slo',
            'departments',
            'status_message_templates',
        )
        filterset_class = CategoryFilterSet
        interfaces = (relay.Node,)
