from rest_framework.renderers import BaseRenderer


class SerializedJsonRenderer(BaseRenderer):
    """
    This renderer is useful when the data source is already serialized JSON.

    It is used, for example, when serialized JSON is extracted from Postgres
    directly while bypassing the Django REST Framework renderers.
    """
    format = 'json'
    media_type = 'application/json'

    def render(self, data, media_type=None, renderer_context=None):
        return data
