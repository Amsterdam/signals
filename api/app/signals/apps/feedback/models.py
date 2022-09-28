# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
import secrets
import uuid
from datetime import timedelta

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone

from signals.apps.feedback.app_settings import FEEDBACK_EXPECTED_WITHIN_N_DAYS
from signals.apps.feedback.managers import FeedbackManager


def generate_token():
    """Use secrets module of Python to generate a UUID object."""
    return uuid.UUID(hex=secrets.token_hex(16))


class StandardAnswerTopic(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=1000)
    order = models.IntegerField(default=0, null=True, blank=True,
                                help_text='De volgorde van de antwoorden '
                                          'onderwerpen voor het KTP proces.')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Standaard antwoord onderwerp'
        verbose_name_plural = 'Standaard antwoorden onderwerpen'


class StandardAnswer(models.Model):
    is_visible = models.BooleanField(default=True)
    is_satisfied = models.BooleanField(default=True)
    reopens_when_unhappy = models.BooleanField(default=False)
    text = models.TextField(max_length=1000, unique=True)
    order = models.IntegerField(default=0, null=True, blank=True,
                                help_text='De volgorde van de antwoorden tijdens het KTO proces. '
                                          'Bij een selectie van een onderwerp is de volgorde van het '
                                          'antwoord binnen het geselecteerde onderwerp.')

    topic = models.ForeignKey(
        StandardAnswerTopic, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        pos_neg = 'POSITIEF' if self.is_satisfied else 'NEGATIEF'
        return f'{pos_neg} : {self.text}'

    class Meta:
        verbose_name = 'Standaard antwoord'
        verbose_name_plural = 'Standaard antwoorden'


class Feedback(models.Model):
    # Bookkeeping
    token = models.UUIDField(db_index=True, primary_key=True, default=generate_token)
    _signal = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, related_name='feedback')
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(editable=False, null=True)

    # Fields that we expect Reporter to fill out
    is_satisfied = models.BooleanField(null=True)
    allows_contact = models.BooleanField(default=False)
    text = models.TextField(max_length=1000, null=True, blank=True)
    text_list = ArrayField(models.TextField(max_length=1000, blank=True), null=True, blank=True)
    text_extra = models.TextField(max_length=1000, null=True, blank=True)

    objects = models.Manager()
    actions = FeedbackManager()

    history_log = GenericRelation('history.Log', object_id_field='object_pk')

    class Meta:
        ordering = ('_signal', '-created_at')

    @property
    def is_too_late(self):
        """
        Feedback still on time
        """
        open_period = timedelta(days=FEEDBACK_EXPECTED_WITHIN_N_DAYS)

        return timezone.now() > self.created_at + open_period

    @property
    def is_filled_out(self):
        """
        Feedback form already filled out and submitted.
        """
        return self.submitted_at is not None


def _get_description_of_receive_feedback(feedback_token):
    """
    Given a history entry for submission of feedback create descriptive text.
    """
    feedback = Feedback.objects.get(token=feedback_token)

    # Craft a message for UI
    desc = 'Ja, de melder is tevreden\n' if feedback.is_satisfied else \
        'Nee, de melder is ontevreden\n'

    text = ",\n". join(feedback.text_list) if feedback.text_list else feedback.text or "Geen Feedback"
    desc += 'Waarom: {}'.format(text)

    if feedback.text_extra:
        desc += '\nToelichting: {}'.format(feedback.text_extra)

    yes_no = 'Ja' if feedback.allows_contact else 'Nee'
    desc += f'\nToestemming contact opnemen: {yes_no}'

    return desc
