from django.conf import settings
from django.test.signals import setting_changed

DEFAULTS = dict(
    FLEX_HORECA=None,
    TOEZICHT_OR_NIEUW_WEST=None,
    VTH_NIEUW_WEST=None,
)


class AppSettings(object):
    def __init__(self, user_settings=None, defaults=None):
        if user_settings:
            self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, 'EMAIL_INTEGRATIONS', {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError('Invalid email_integrations setting: {}'.format(attr))

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


app_settings = AppSettings(None, DEFAULTS)


def reload_app_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == 'EMAIL_INTEGRATIONS':
        app_settings.reload()


setting_changed.connect(reload_app_settings)
