from django.contrib.postgres.search import SearchVector, SearchRank, SearchQuery
from django.db import models


class SignalSearchManager(models.Manager):
    def filter_by_query(self, query):
        query = SearchQuery(query)

        search_vectors = (
                SearchVector('text', weight='A') +
                SearchVector('category_assignment__sub_category__name', weight='B') +
                SearchVector('category_assignment__sub_category__main_category__name', weight='D')
        )

        qs = self.get_queryset().select_related(
            'location',
            'status',
            'category_assignment',
            'category_assignment__sub_category__main_category',
            'reporter',
            'priority',
            'parent',
        ).prefetch_related(
            'category_assignment__sub_category__departments',
            'children',
            'attachments',
            'notes',
        )

        return qs.annotate(
            search=search_vectors,
            rank=SearchRank(
                vector=search_vectors,
                query=query
            ),
        ).filter(
            rank__gte=0.3
        ).order_by(
            '-rank'
        )
