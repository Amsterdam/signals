from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class LinkHeaderPagination(PageNumberPagination):
    page_size = 4000  # 2.5 times the average signals made in a day, at this moment the highest average is 1600
    page_size_query_param = 'page_size'

    def get_pagination_headers(self):
        headers = {'X-Total-Count': self.page.paginator.count, 'Link': []}
        next_link = self.get_next_link()

        header_links = []
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
