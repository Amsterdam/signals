# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone

from signals.apps.feedback.app_settings import FEEDBACK_EXPECTED_WITHIN_N_DAYS
from signals.apps.signals.tokens.token_generator import TokenGenerator


class StandardAnswerTopic(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=1000)
    order = models.IntegerField(default=0, null=True, blank=True,
                                help_text='De volgorde van de antwoorden '
                                          'onderwerpen voor het KTP proces.')

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = 'Standaard antwoord onderwerp'
        verbose_name_plural = 'Standaard antwoorden onderwerpen'


class StandardAnswer(models.Model):
    is_visible = models.BooleanField(default=True)
    is_satisfied = models.BooleanField(default=True)
    reopens_when_unhappy = models.BooleanField(default=False,
                                               help_text='Als deze optie is aangevinkt, zal een '
                                                         'melding heropend worden. Let op, bij '
                                                         'een "open answer" wordt de melding altijd '
                                                         'automatisch heropend.')
    text = models.TextField(max_length=1000, unique=True)
    order = models.IntegerField(default=0, null=True, blank=True,
                                help_text='De volgorde van de antwoorden tijdens het KTO proces. '
                                          'Bij een selectie van een onderwerp is de volgorde van het '
                                          'antwoord binnen het geselecteerde onderwerp.')

    topic = models.ForeignKey(StandardAnswerTopic, null=True, blank=True, on_delete=models.SET_NULL)

    open_answer = models.BooleanField(default=False,
                                      help_text='Als deze optie is aangevinkt, dan wordt een open '
                                                'antwoord verwacht van de melder en is de opgegeven '
                                                'tekst een default waarde. De melding wordt bij deze '
                                                'optie automatisch heropend. ')

    def __str__(self) -> str:
        pos_neg = 'POSITIEF' if self.is_satisfied else 'NEGATIEF'
        return f'{pos_neg} : {self.text}'

    class Meta:
        verbose_name = 'Standaard antwoord'
        verbose_name_plural = 'Standaard antwoorden'


class Feedback(models.Model):
    # Bookkeeping
    token = models.CharField(max_length=120, primary_key=True, default=TokenGenerator())

    _signal = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, related_name='feedback')
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(editable=False, null=True)

    # Fields that we expect Reporter to fill out
    is_satisfied = models.BooleanField(null=True)
    allows_contact = models.BooleanField(default=False)
    text = models.TextField(max_length=1000, null=True, blank=True)
    text_list = ArrayField(models.TextField(max_length=1000, blank=True), null=True, blank=True)
    text_extra = models.TextField(max_length=1000, null=True, blank=True)

    history_log = GenericRelation('history.Log', object_id_field='object_pk')

    class Meta:
        ordering = ('_signal', '-created_at')

    @property
    def is_too_late(self) -> bool:
        """
        Feedback still on time
        """
        open_period = timedelta(days=FEEDBACK_EXPECTED_WITHIN_N_DAYS)

        return timezone.now() > self.created_at + open_period

    @property
    def is_filled_out(self) -> bool:
        """
        Feedback form already filled out and submitted.
        """
        return self.submitted_at is not None

    def get_description(self) -> str:
        """
        Description is used for logging a description of the feedback in the history log.
        """
        if self.is_satisfied:
            description = 'Ja, de melder is tevreden'
        else:
            description = 'Nee, de melder is ontevreden'

        if self.text_list:
            why = ',\n'.join(self.text_list)
        elif self.text:
            why = self.text
        else:
            why = 'Geen Feedback'

        description = f'{description}\n' \
                      f'Waarom: {why}' \

        if self.text_extra:
            description = f'{description}\n' \
                          f'Toelichting: {self.text_extra}'

        description = f'{description}\n' \
                      f'Toestemming contact opnemen: {"Ja" if self.allows_contact else "Nee"}'

        return description

    def get_frontend_positive_feedback_url(self):
        return f'{settings.FRONTEND_URL}/kto/ja/{self.token}'

    def get_frontend_negative_feedback_url(self):
        return f'{settings.FRONTEND_URL}/kto/nee/{self.token}'
