# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django.contrib.gis.db import models


class Question(models.Model):
    ASSET_SELECT = 'asset_select'
    CATERPILLAR_SELECT = 'caterpillar_select'
    CHECKBOX_INPUT = 'checkbox_input'
    CLOCK_SELECT = 'clock_select'
    DATE_TIME_INPUT = 'date_time_input'
    QUESTION_HEADER = 'question_header'
    LOCATION_SELECT = 'location_select'
    PLAIN_TEXT = 'plain_text'
    RADIO_INPUT = 'radio_input'
    SELECT_INPUT = 'select_input'
    STREETLIGHT_SELECT = 'streetlight_select'
    TEXT_INPUT = 'text_input'
    TEXT_AREA_INPUT = 'text_area_input'

    FIELD_TYPE_CHOICES = (
        (ASSET_SELECT, 'AssetSelectRenderer'),
        (CATERPILLAR_SELECT, 'CaterpillarSelectRenderer'),
        (CHECKBOX_INPUT, 'CheckboxInput'),
        (CLOCK_SELECT, 'ClockSelectRenderer'),
        (DATE_TIME_INPUT, 'DateTimeInput'),
        (QUESTION_HEADER, 'QuestionHeader'),
        (LOCATION_SELECT, 'AssetSelectRenderer'),
        (PLAIN_TEXT, 'PlainText'),
        (RADIO_INPUT, 'RadioInputGroup'),
        (SELECT_INPUT, 'SelectInput'),
        (STREETLIGHT_SELECT, 'StreetlightSelectRenderer'),
        (TEXT_INPUT, 'TextInput'),
        (TEXT_AREA_INPUT, 'TextareaInput'),
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
