# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
import uuid

from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from pytz import utc

from signals.apps.signals.managers import SignalManager
from signals.apps.signals.models.mixins import CreatedUpdatedModel
from signals.apps.signals.querysets import SignalQuerySet


class Signal(CreatedUpdatedModel):
    SOURCE_DEFAULT_ANONYMOUS_USER = 'online'

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    source = models.CharField(max_length=128, default=SOURCE_DEFAULT_ANONYMOUS_USER)
    text = models.CharField(max_length=3000)
    text_extra = models.CharField(max_length=10000, default='', blank=True)
    incident_date_start = models.DateTimeField(null=False)  # Date of the incident.
    incident_date_end = models.DateTimeField(null=True)  # Date of the incident.
    operational_date = models.DateTimeField(null=True)  # Date action is expected
    expire_date = models.DateTimeField(null=True)  # Date we should have reported back to reporter.
    extra_properties = models.JSONField(null=True)

    # Assignments
    parent = models.ForeignKey(to='self', related_name='children', null=True, blank=True, on_delete=models.SET_NULL)

    location = models.OneToOneField('signals.Location', related_name='signal', null=True, on_delete=models.SET_NULL)

    status = models.OneToOneField('signals.Status', related_name='signal', null=True, on_delete=models.SET_NULL)

    category_assignment = models.OneToOneField('signals.CategoryAssignment', related_name='signal', null=True,
                                               on_delete=models.SET_NULL)

    categories = models.ManyToManyField('signals.Category', through='signals.CategoryAssignment')

    reporter = models.OneToOneField('signals.Reporter', related_name='signal', null=True, on_delete=models.SET_NULL)

    priority = models.OneToOneField('signals.Priority', related_name='signal', null=True, on_delete=models.SET_NULL)

    directing_departments_assignment = models.OneToOneField('signals.SignalDepartments',
                                                            related_name='directing_department_signal', null=True,
                                                            on_delete=models.SET_NULL)

    routing_assignment = models.OneToOneField('signals.SignalDepartments', related_name='routing_signal', null=True,
                                              on_delete=models.SET_NULL)

    user_assignment = models.OneToOneField('signals.SignalUser', related_name='user_assignment_signal', null=True,
                                           on_delete=models.SET_NULL)

    type_assignment = models.OneToOneField('signals.Type', related_name='signal', null=True, on_delete=models.SET_NULL)

    # Managers
    objects = SignalQuerySet.as_manager()
    actions = SignalManager()

    class Meta:
        permissions = (
            ('sia_read', 'Leesrechten algemeen'),  # SIG-2192
            ('sia_write', 'Schrijfrechten algemeen'),  # SIG-2194
            ('sia_split', 'Splitsen van een melding'),  # SIG-2192
            ('sia_signal_create_initial', 'Melding aanmaken'),  # SIG-2192
            ('sia_signal_create_note', 'Notitie toevoegen bij een melding'),  # SIG-2192
            ('sia_signal_change_status', 'Wijzigen van status van een melding'),  # SIG-2192
            ('sia_signal_change_category', 'Wijzigen van categorie van een melding'),  # SIG-2192
            ('sia_signal_export', 'Meldingen exporteren'),  # SIG-2192
            ('sia_signal_report', 'Rapportage beheren'),  # SIG-2192
        )
        ordering = ('created_at',)
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['id', 'parent']),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.uuid:
            self.uuid = uuid.uuid4()

    def __str__(self):
        """
        Identifying string.
        DO NOT expose sensitive stuff here.
        """
        # Fix for bug SIG-2486 Timezones were not consistently shown
        created_at = self.created_at
        field_timezone = timezone.get_current_timezone() if settings.USE_TZ else None
        if timezone.is_aware(created_at) and field_timezone:
            created_at = created_at.astimezone(field_timezone)
        elif timezone.is_aware(created_at):
            created_at = timezone.make_naive(created_at, utc)

        return f'{self.id} - ' \
               f'{self.status.state if self.status else ""} - ' \
               f'{self.location.buurt_code if self.location else ""} - ' \
               f'{created_at.isoformat()}'

    @property
    def is_parent(self):
        return self.children.exists()

    @property
    def is_child(self):
        return self.parent is not None

    def get_id_display(self):
        """
        Signals Identifier used for external communication.
        Can be configured in the settings, defaults to 'SIG-' + id.
        """
        return f'{settings.SIGNAL_ID_DISPLAY_PREFIX or ""}{self.id}'

    @property
    def sia_id(self):
        """
        Deprecated in favour of `id_display`. Will be removed a.s.a.p.

        TODO:
        - Check if this can be changed in the SIGMAX communication
        - Remove this property

        SIA identifier used for external communication.
        """
        return f'SIA-{self.id}'

    @property
    def siblings(self):
        """
        Returns all siblings, excluded the signal itself. By default it will return a Signal.objects.none()
        """
        if self.is_child:
            return self.parent.children.exclude(pk=self.pk) if self.pk else self.parent.children.all()
        return self.__class__.objects.none()

    def _validate(self):
        if self.is_parent and self.is_child:
            # We cannot be a parent and a child at once
            raise ValidationError('Cannot be a parent and a child at the once')

        if self.parent and self.parent.is_child:
            # The parent of this Signal cannot be a child of another Signal
            raise ValidationError('A child of a child is not allowed')

        if (self.pk is None and self.is_child and
                self.siblings.count() >= settings.SIGNAL_MAX_NUMBER_OF_CHILDREN):
            # we are a new child and our parent already has the max number of children
            raise ValidationError('Maximum number of children reached for the parent Signal')

    def save(self, *args, **kwargs):
        self._validate()
        super().save(*args, **kwargs)
