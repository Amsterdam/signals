from django.contrib.gis.db import models


class CategoryQuestion(models.Model):
    category = models.ForeignKey('signals.Category', on_delete=models.CASCADE)
    question = models.ForeignKey('signals.Question', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(null=True)
