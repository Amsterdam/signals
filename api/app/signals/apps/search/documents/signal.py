import logging

from elasticsearch_dsl import Date, InnerDoc, Keyword, Nested, Object, Text
from elasticsearch_dsl.query import Bool

from signals.apps.search.documents.base import DocumentBase
from signals.apps.signals.models import Signal

log = logging.getLogger(__name__)


class Department(InnerDoc):
    code = Keyword()
    name = Text(analyzer='standard')
    is_intern = Bool()


class ParentCategory(InnerDoc):
    name = Text(analyzer='standard')
    slug = Text(analyzer='standard')


class Category(InnerDoc):
    name = Text(analyzer='standard')
    slug = Text(analyzer='standard')
    departments = Nested(Department)
    parent = Object(ParentCategory)


class CategoryAssignment(InnerDoc):
    category = Object(Category)
    extra_properties = Text(analyzer='standard')


class Priority(InnerDoc):
    priority = Text(analyzer='standard')


class Reporter(InnerDoc):
    email = Text(analyzer='standard')
    phone = Text(analyzer='standard')


class SignalDocument(DocumentBase):
    _display = Keyword()
    id = Text(analyzer='standard')
    signal_id = Text(analyzer='standard')
    text = Text(analyzer='standard')
    incident_date_start = Date()

    main_category = Text(analyzer='standard')
    sub_category = Text(analyzer='standard')

    category = Object(Category)
    reporter = Object(Reporter)
    priority = Object(Priority)

    created_at = Date()
    updated_at = Date()

    class Index:
        name = 'signals'
        using = 'default'

    def get_model(self):
        return Signal

    def get_queryset(self):
        return self.get_model().objects.select_related(
            'location',
            'status',
            'category_assignment',
            'category_assignment__category',
            'category_assignment__category__parent',
            'reporter',
            'priority',
            'parent',
        ).prefetch_related(
            'category_assignment__category__departments',
            'children',
            'attachments',
            'notes',
        ).all()

    @classmethod
    def create_document(cls, obj):
        category_assignment = None
        if obj.category_assignment:
            category_assignment = obj.category_assignment

        return SignalDocument(
            meta=dict(
                id=obj.id,
            ),
            _display=str(obj),
            id=obj.id,
            signal_id=obj.signal_id,
            text=obj.text,
            incident_date_start=obj.incident_date_start,
            category_assignment={
                'category': {
                    'name': category_assignment.category.name,
                    'slug': category_assignment.category.slug,
                    'departments': [{
                        'code': department.code,
                        'name': department.name,
                        'is_intern': department.is_intern,
                    } for department in category_assignment.category.departments.iterator()],
                    'parent': {
                        'name': category_assignment.category.parent.name,
                        'slug': category_assignment.category.parent.slug,
                    } if category_assignment.category.parent else None
                },
                'extra_properties': category_assignment.extra_properties,
            } if category_assignment else None,
            reporter={
                'email': obj.reporter.email if obj.reporter.email else '',
                'phone': obj.reporter.phone if obj.reporter.phone else '',
            } if obj.reporter else None,
            priority={
                'priority': obj.priority.priority if obj.priority else None,
            },
            type={
                'code': obj.type_assignment.name if obj.type_assignment else None,
            },
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    def create_document_dict(self):
        return self.to_dict(include_meta=True)
