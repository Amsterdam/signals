# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.
from typing import Any

from import_export import fields, resources

from signals.apps.signals.models import Category, CategoryDepartment, Department


class DepartmentResource(resources.ModelResource):
    categories = fields.Field(column_name='categories')

    def dehydrate_categories(self, department: Department) -> str:
        # Returns a string like: "CAT1|True|False, CAT2|False|True"
        return ', '.join(
            f"{cd.category.slug}|{cd.is_responsible}|{cd.can_view}"
            for cd in department.categorydepartment_set.all()
        )

    class Meta:
        model = Department
        import_id_fields = ('code',)
        exclude = ('id',)

    def after_save_instance(self, instance: Department, row: dict[str, Any], **kwargs: Any) -> None:
        dry_run = kwargs.get('dry_run', False)

        if dry_run:
            return

        categories = row.get('categories', '')
        CategoryDepartment.objects.filter(department=instance).delete()
        for item in [v.strip() for v in categories.split(',') if v.strip()]:
            try:
                category_slug, is_responsible, can_view = item.split('|')
                category = Category.objects.get(slug=category_slug)

                CategoryDepartment.objects.create(
                    category=category,
                    department=instance,
                    is_responsible=is_responsible.lower() == 'true',
                    can_view=can_view.lower() == 'true'
                )
            except Exception:
                continue
