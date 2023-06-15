# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from django.core.paginator import InvalidPage, Page, Paginator
from rest_framework.exceptions import NotFound

from signals.apps.api.generics.pagination import HALPagination


class ElasticPage(Page):
    """Page for Elasticsearch."""

    def __init__(self, object_list, number, paginator):
        self.count = paginator.object_list._response.hits.total
        super().__init__(object_list, number, paginator)


class ElasticPaginator(Paginator):
    """Paginator for Elasticsearch."""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def page(self, number):
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        response = self.object_list[bottom:top].execute()
        qs = self.object_list.to_queryset(response, user=self.user)
        return self._get_page(qs, number, self)

    def _get_page(self, *args, **kwargs):
        return ElasticPage(*args, **kwargs)


class ElasticHALPagination(HALPagination):
    """Paginator for Elasticsearch."""

    django_paginator_class = ElasticPaginator

    def paginate_queryset(self, queryset, request, view=None):
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size, user=request.user)
        page_number = int(request.query_params.get(self.page_query_param, 1))
        if page_number in self.last_page_strings:
            page_number = paginator.num_pages

        try:
            self.page = paginator.page(page_number)
        except InvalidPage:
            raise NotFound(self.invalid_page_message)

        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True

        self.request = request
        return list(self.page)
