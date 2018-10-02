from signals.utils.ip import get_ip


class AddExtrasMixin:
    """Mixin class to add extra values to the validated data."""

    def add_extra_properties(self, data):
        ip = get_ip(self.context.get('request'))
        if ip:
            extra_properties = data['extra_properties'] if 'extra_properties' in data else {}
            extra_properties['IP'] = ip
            data['extra_properties'] = extra_properties
        return data

    def add_user(self, data):
        request = self.context.get('request')
        if request.user and not request.user.is_anonymous:
            data['user'] = request.user.get_username()
        return data
