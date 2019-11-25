import logging

from django.db.models import Case, When
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Document, Index, Search

log = logging.getLogger(__name__)


class CustomSearch(Search):

    def __init__(self, **kwargs):
        self._queryset = kwargs.pop('queryset', None)
        super(CustomSearch, self).__init__(**kwargs)

    def _clone(self):
        s = super(CustomSearch, self)._clone()
        s._queryset = self._queryset
        return s

    def to_queryset(self, response=None, keep_order=True, user=None):
        response = response if response else self._response

        pks = [result.id for result in response.hits]
        qs = self._queryset.filter(pk__in=pks)

        if keep_order:
            preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pks)])
            qs = qs.order_by(preserved_order)

        return qs.filter_for_user(user=user) if user else qs


class DocumentBase(Document):
    def get_queryset(self):
        return self.get_model().objects.all()

    @classmethod
    def search(cls, using=None, index=None):
        return CustomSearch(
            using=cls._get_using(using),
            index=cls._default_index(index),
            doc_type=[cls],
            queryset=cls().get_queryset(),
        )

    @classmethod
    def clear_index(cls, index=None):
        index_instance = Index(cls._default_index(index))
        if index_instance.exists():
            index_instance.delete()

    @classmethod
    def prepare_batch(cls, queryset):
        for obj in queryset.iterator():
            yield cls().create_document(obj).create_document_dict()

    @classmethod
    def bulk(cls, queryset, size, using=None):
        es = cls._get_connection(using)
        for start in range(0, queryset.count(), size):
            end = start + size
            bulk(
                client=es,
                actions=cls.prepare_batch(queryset[start:end]),
                chunk_size=size,
            )

    @classmethod
    def index_documents(cls, index=None, using=None, batch=1000):
        cls.init(index, using)
        cls.bulk(cls().get_queryset(), batch, using)
