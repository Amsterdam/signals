from django.conf import settings
from django.test.signals import setting_changed

DEFAULTS = {
    # Pagination
    'PAGE_SIZE': 100,
    'ELASTIC': {
        'connections': {
            'default': {
                'hosts': ['http://127.0.0.1:9200', ]
            }
        }
    },
}


class APISettings(object):
    def __init__(self, user_settings=None, defaults=None):
        if user_settings:
            self._user_settings = self.__check_user_settings(user_settings)
        self.defaults = defaults or DEFAULTS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, 'SEARCH_SETTINGS', {})
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


search_settings = APISettings(None, DEFAULTS)


def reload_search_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == 'SEARCH_SETTINGS':
        search_settings.reload()


setting_changed.connect(reload_search_settings)
