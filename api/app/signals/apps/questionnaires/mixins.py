# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam


class HyperlinkedRelatedFieldMixin:
    def get_url(self, obj, view_name, *args, **kwargs):
        request = self.context.get('request')
        namespace = request.resolver_match.namespace if request else None
        if namespace:
            view_name = f'{namespace}:{view_name}'
        return super().get_url(obj=obj, view_name=view_name, request=request, format=self.context.get('format'))

    def _reverse(self, view_name, kwargs):
        request = self.context.get('request')
        namespace = request.resolver_match.namespace if request else None
        if namespace:
            view_name = f'{namespace}:{view_name}'
        return self.reverse(view_name, kwargs=kwargs, request=request, format=self.context.get('format'))
