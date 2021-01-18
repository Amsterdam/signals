# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django.contrib.gis.db import models


class Question(models.Model):
    PLAIN_TEXT = 'plain_text'
    TEXT_INPUT = 'text_input'
    MULTI_TEXT_INPUT = 'multi_text_input'
    CHECKBOX_INPUT = 'checkbox_input'
    RADIO_INPUT = 'radio_input'
    SELECT_INPUT = 'select_input'
    TEXT_AREA_INPUT = 'text_area_input'
    MAP_SELECT = 'map_select'

    FIELD_TYPE_CHOICES = (
        (PLAIN_TEXT, 'PlainText'),
        (TEXT_INPUT, 'TextInput'),
        (MULTI_TEXT_INPUT, 'MultiTextInput'),
        (CHECKBOX_INPUT, 'CheckboxInput'),
        (RADIO_INPUT, 'RadioInput'),
        (SELECT_INPUT, 'SelectInput'),
        (TEXT_AREA_INPUT, 'TextareaInput'),
        (MAP_SELECT, 'MapSelect'),
    )

    key = models.CharField(max_length=255)
    field_type = models.CharField(max_length=32, choices=FIELD_TYPE_CHOICES, default=PLAIN_TEXT)
    meta = models.JSONField(blank=True, default=dict)
    required = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Questions'

    def __str__(self):
        """String representation."""
        return '{key} - {meta}'.format(key=self.key, meta=self.meta)
