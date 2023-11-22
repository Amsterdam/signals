# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from collections import OrderedDict

from datapunt_api.serializers import LinksField
from rest_framework.reverse import reverse

from signals.apps.signals.models import StoredSignalFilter


class StoredSignalFilterLinksField(LinksField):
    def to_representation(self, stored_signal_filter: StoredSignalFilter) -> OrderedDict:
        request = self.context.get('request')

        filter_url = reverse('private-signals-list', request=request)
        url_safe_options = stored_signal_filter.url_safe_options()
        if url_safe_options:
            filter_url = '{}?{}'.format(filter_url, url_safe_options)

        result = OrderedDict([
            ('curies', {'name': 'sia', 'href': reverse('signal-namespace', request=request)}),
            ('self', {'href': self.get_url(stored_signal_filter, 'stored-signal-filters-detail', request, None)}),
            ('sia:filter', {'href': filter_url}),
        ])

        return result
