from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class LinkHeaderPagination(PageNumberPagination):
    page_size_query_param = 'page_size'

    def __init__(self, page_query_param=None, page_size=None, *args, **kwargs):
        super(LinkHeaderPagination, self).__init__(*args, **kwargs)

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
