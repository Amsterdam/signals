"""
Translation table of old to new categories (to allow automatic reassignment).

Note:
- This allows decoupled deployment of signals backend and accompanying machine
  learning model in case of category re-assignments.
"""
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError

from signals.apps.signals.models.mixins import CreatedUpdatedModel
from signals.apps.signals.models.category import Category


class CategoryTranslation(CreatedUpdatedModel):
    created_by = models.EmailField(null=True, blank=True)
    text = models.CharField(max_length=10000, null=True, blank=True)
    old_category = models.ForeignKey(Category, unique=True)
    new_category = models.ForeignKey(Category)

    def clean(self):
        if self.old_category == self.new_category:
            raise ValidationError('Cannot have old and new category the same.')
        if not self.new_category.is_active:
            raise ValidationError('New category must be active')
