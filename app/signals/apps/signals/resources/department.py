from import_export import resources, fields

from signals.apps.signals.models import Department, CategoryDepartment, Category


class DepartmentResource(resources.ModelResource):
    categories = fields.Field(column_name='categories')

    def dehydrate_categories(self, department):
        # Returns a string like: "CAT1|True|False, CAT2|False|True"
        return ', '.join(
            f"{cd.category.slug}|{cd.is_responsible}|{cd.can_view}"
            for cd in department.categorydepartment_set.all()
        )

    class Meta:
        model = Department

    def after_save_instance(self, instance, row, **kwargs):
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