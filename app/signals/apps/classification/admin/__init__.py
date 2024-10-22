from django.contrib import admin

from signals.apps.classification.admin.admins import TrainingSetAdmin, ClassifierAdmin
from signals.apps.classification.models import TrainingSet
from signals.apps.classification.models.classifier import Classifier

admin.site.register(TrainingSet, TrainingSetAdmin)
admin.site.register(Classifier, ClassifierAdmin)

