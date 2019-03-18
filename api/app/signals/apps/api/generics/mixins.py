class AddExtrasMixin:
    """Mixin class to add extra values to the validated data."""

    def add_user(self, data):
        request = self.context.get('request')
        if request.user and not request.user.is_anonymous:
            data['user'] = request.user.get_username()
        return data
