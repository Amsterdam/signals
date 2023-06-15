# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from datapunt_api.pagination import HALPagination as DataPuntHALPagination
from django.core.paginator import InvalidPage
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class HALPagination(DataPuntHALPagination):
    def get_paginated_response_schema(self, schema: dict) -> dict:
        return {
            'type': 'object',
            'properties': {
                '_links': {
                    'type': 'object',
                    'properties': {
                        'self': {
                            'type': 'object',
                            'properties': {
                                'href': {
                                    'type': 'string',
                                    'nullable': True,
                                    'format': 'uri',
                                    'example': f'http://api.example.org/endpoint/?{self.page_query_param}=3'
                                },
                            },
                        },
                        'next': {
                            'type': 'object',
                            'properties': {
                                'href': {
                                    'type': 'string',
                                    'nullable': True,
                                    'format': 'uri',
                                    'example': f'http://api.example.org/endpoint/?{self.page_query_param}=4'
                                },
                            },
                        },
                        'previous': {
                            'type': 'object',
                            'properties': {
                                'href': {
                                    'type': 'string',
                                    'nullable': True,
                                    'format': 'uri',
                                    'example': f'http://api.example.org/endpoint/?{self.page_query_param}=2'
                                },
                            },
                        }
                    }
                },
                'count': {
                    'type': 'integer',
                    'example': 123,
                },
                'results': schema,
            },
        }


class LinkHeaderPagination(PageNumberPagination):
    page_size_query_param = 'page_size'

    def __init__(self, page_query_param=None, page_size=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.page_query_param = page_query_param or self.page_query_param
        self.page_size = page_size or self.page_size

    def get_pagination_headers(self):
        headers = {'X-Total-Count': self.page.paginator.count, 'Link': []}
        next_link = self.get_next_link()

        header_links = [f'<{self.request.build_absolute_uri()}>; rel="self"']
        if next_link:
            header_links.append(f'<{next_link}>; rel="next"')

        previous_link = self.get_previous_link()
        if previous_link:
            header_links.append(f'<{previous_link}>; rel="prev"')

        if header_links:
            headers['Link'] = ','.join(header_links)
        else:
            headers['Link'] = {}

        return headers

    def get_paginated_response(self, data):
        return Response(data, headers=self.get_pagination_headers())


class LinkHeaderPaginationForQuerysets(LinkHeaderPagination):
    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        # Note copied from rest_framework.pagination.PageNumberPagination, but
        # adapted to not return a list - this is needed to paginate in DB and
        # later aggregate in DB (used for map generation).
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = self.get_page_number(request, paginator)

        try:
            self.page = paginator.page(page_number)
        except InvalidPage:
            raise NotFound(self.invalid_page_message)

        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        self.request = request
        return self.page.object_list
