from import_export import resources, fields, widgets

from signals.apps.signals.models import Category

class CategoryResource(resources.ModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=widgets.ForeignKeyWidget(Category, 'slug')
    )

    class Meta:
        model = Category
        exclude = ('slug', 'departments', 'questions', 'questionnaire', )
