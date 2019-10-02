"""
Translation table of old to new categories (to allow automatic reassignment).

Note:
- This allows decoupled deployment of signals backend and accompanying machine
  learning model in case of category re-assignments.
"""
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import DO_NOTHING

from signals.apps.signals.models.category import Category
from signals.apps.signals.models.mixins import CreatedUpdatedModel


class CategoryTranslation(CreatedUpdatedModel):
    created_by = models.EmailField(null=True, blank=True)
    text = models.CharField(max_length=10000, null=True, blank=True)
    old_category = models.ForeignKey(Category, on_delete=DO_NOTHING, related_name='translations')
    new_category = models.ForeignKey(Category, on_delete=DO_NOTHING, related_name='+')

    def clean(self):
        if self.old_category == self.new_category:
            raise ValidationError('Cannot have old and new category the same.')
        if not self.new_category.is_active:
            raise ValidationError('New category must be active')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Zet categorie "{self.old_category.slug}" om naar "{self.new_category.slug}"'

    class Meta:
        verbose_name = 'categorie omzetting'
        verbose_name_plural = 'categorie omzettingen'
