# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from collections import OrderedDict

from rest_framework import serializers


class StoredSignalFilterLinksField(serializers.HyperlinkedIdentityField):
    def to_representation(self, stored_signal_filter):
        request = self.context.get('request')

        filter_url = self.reverse('private-signals-list', request=request)
        url_safe_options = stored_signal_filter.url_safe_options()
        if url_safe_options:
            filter_url = '{}?{}'.format(filter_url, url_safe_options)

        result = OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request))),
            ('self', dict(href=self.get_url(stored_signal_filter, 'stored-signal-filters-detail', request, None))),  # noqa
            ('sia:filter', dict(href=filter_url)),
        ])

        return result
