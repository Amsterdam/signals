# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.

from import_export import fields, resources, widgets

from signals.apps.signals.models import Category


class CategoryResource(resources.ModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=widgets.ForeignKeyWidget(Category, 'slug')
    )

    class Meta:
        model = Category
        import_id_fields = ('slug',)
        exclude = ('id', 'departments', 'questions', 'questionnaire', )
