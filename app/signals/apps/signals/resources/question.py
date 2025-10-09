# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.

from import_export import fields, resources

from signals.apps.signals.models import Category, CategoryQuestion, Question


class QuestionResource(resources.ModelResource):
    categories = fields.Field(column_name='categories')

    def dehydrate_categories(self, question):
        # Returns a string like: "CAT1|1, CAT1|2"
        return ', '.join(
            f"{cq.category.slug}|{cq.order or 0}"
            for cq in question.categoryquestion_set.all()
        )

    class Meta:
        model = Question
        import_id_fields = ('key',)
        exclude = ('id',)

    def after_save_instance(self, instance, row, **kwargs):
        dry_run = kwargs.get('dry_run', False)

        if dry_run:
            return

        categories = row.get('categories', '')
        CategoryQuestion.objects.filter(question=instance).delete()
        for item in [v.strip() for v in categories.split(',') if v.strip()]:
            try:
                category_slug, order = item.split('|')
                category = Category.objects.get(slug=category_slug)

                CategoryQuestion.objects.create(
                    category=category,
                    question=instance,
                    order=int(order)
                )
            except Exception:
                continue
