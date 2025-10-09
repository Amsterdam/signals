from import_export import resources

from signals.apps.signals.models import Question


class QuestionResource(resources.ModelResource):
    # TODO: Categories mee exporteren en importeren, incl order (through table)?

    class Meta:
        model = Question
