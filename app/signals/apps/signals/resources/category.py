from import_export import resources, fields, widgets

from signals.apps.signals.models import Category, Department, Question


class CategoryResource(resources.ModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=widgets.ForeignKeyWidget(Category, 'slug')
    )

    departments = fields.Field(
        column_name='departments',
        attribute='departments',
        widget=widgets.ManyToManyWidget(Department, field='code'),
    )

    questions = fields.Field(
        column_name='questions',
        attribute='questions',
        widget=widgets.ManyToManyWidget(Question, field='key'),
    )

    # TODO: Questionnaires mee exporteren en importeren
    # TODO: StatusMessages mee exporteren en importeren
    # TODO: is_responsible en can_view mee exporteren en importeren van het CategoryDepartment model
    # TODO: order mee exporteren en importeren van het CategoryQuestion model

    class Meta:
        model = Category
        exclude = ('slug', )
