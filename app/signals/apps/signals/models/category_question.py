# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django.contrib.gis.db import models


class CategoryQuestion(models.Model):
    category = models.ForeignKey('signals.Category', on_delete=models.CASCADE)
    question = models.ForeignKey('signals.Question', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(null=True)
