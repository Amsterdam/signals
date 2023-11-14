# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.conf import settings
from django.test.signals import setting_changed

DEFAULTS = dict(
    PAGE_SIZE=100,
    CONNECTION=dict(
        HOST='http://127.0.0.1:9200',
        INDEX='signals',
    ),
    TIMEOUT=10,
)


class APISettings(object):
    def __init__(self, user_settings=None, defaults=None):
        if user_settings:
            self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, 'SEARCH', {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError('Invalid SEARCH setting: {}'.format(attr))

        try:
            val = self.user_settings[attr]
        except KeyError:
            val = self.defaults[attr]

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, '_user_settings'):
            delattr(self, '_user_settings')


app_settings = APISettings(None, DEFAULTS)


def reload_search_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == 'SEARCH':
        app_settings.reload()


setting_changed.connect(reload_search_settings)
