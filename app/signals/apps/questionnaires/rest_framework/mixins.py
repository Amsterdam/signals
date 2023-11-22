# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
from typing import Any, Mapping

from django.db.models import Model
from rest_framework.reverse import reverse


class LinksFieldMixin:
    def _get_url(self, obj: Model, view_name: str) -> str | None:
        request = self.context.get('request')
        namespace = request.resolver_match.namespace if request else None
        if namespace:
            view_name = f'{namespace}:{view_name}'
        return super().get_url(obj=obj, view_name=view_name, request=request, format=self.context.get('format'))

    def _reverse(self, view_name: str, kwargs: Mapping[str, Any]) -> str:
        request = self.context.get('request')
        namespace = request.resolver_match.namespace if request else None
        if namespace:
            view_name = f'{namespace}:{view_name}'
        return reverse(view_name, kwargs=kwargs, request=request, format=self.context.get('format'))
