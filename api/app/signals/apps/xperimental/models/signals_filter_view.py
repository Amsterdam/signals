# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.conf import settings
from django.contrib.gis.db import models
from django.utils import timezone
from pytz import utc

from signals.apps.signals.workflow import STATUS_CHOICES
from signals.apps.xperimental.models.querysets import SignalFilterViewQuerySet


class SignalFilterView(models.Model):
    """
    This Model interacts with the signal_filter_view database view

    The purpose of this database view is to speed up the filtering and rendering of the Signals list response
    """
    # Used for filtering (and partial for rendering the response)
    signal_id = models.IntegerField(primary_key=True)

    source = models.CharField(max_length=128)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    incident_date_start = models.DateTimeField()

    is_signal = models.BooleanField()
    is_parent = models.BooleanField()
    has_changed_children = models.BooleanField()
    is_child = models.BooleanField()

    parent_category_id = models.IntegerField()
    parent_category_slug = models.CharField(max_length=50)

    child_category_id = models.IntegerField()
    child_category_slug = models.CharField(max_length=50)

    category_assignment_deadline = models.DateTimeField()
    category_assignment_deadline_factor_3 = models.DateTimeField()

    status_state = models.CharField(max_length=20, blank=True, choices=STATUS_CHOICES)

    priority_priority = models.CharField(max_length=10)

    location_buurt_code = models.CharField(max_length=4)
    location_address_text = models.CharField(max_length=255)
    location_area_code = models.CharField(max_length=255)
    location_area_code_type = models.CharField(max_length=255)
    location_stadsdeel = models.CharField(max_length=1)

    reporter_email = models.CharField(max_length=254)
    reporter_phone = models.CharField(max_length=17)

    type_name = models.CharField(max_length=3)

    assigned_user_email = models.EmailField(null=True, blank=True)

    directing_departments_assignment = models.OneToOneField('signals.SignalDepartments', related_name='+', null=True,
                                                            on_delete=models.DO_NOTHING)

    feedback_is_satisfied = models.BooleanField(null=True, blank=True)
    feedback_created_at = models.DateTimeField(null=True, blank=True)
    feedback_submitted_at = models.DateTimeField(null=True, blank=True)

    # Used for rendering the response
    text = models.TextField()
    text_extra = models.TextField(null=True, blank=True)
    incident_date_end = models.DateTimeField()

    # Fields are used by the services/domain/permissions/util.py to check User permission therefore they are also needed
    # on this model
    parent_category_name = models.CharField(max_length=255)
    child_category_name = models.CharField(max_length=255)
    category_assignment = models.ForeignKey(to='signals.CategoryAssignment', related_name='+',
                                            on_delete=models.DO_NOTHING)
    routing_assignment = models.OneToOneField('signals.SignalDepartments', related_name='+', null=True,
                                              on_delete=models.DO_NOTHING)  # Also used for filtering

    objects = SignalFilterViewQuerySet.as_manager()

    class Meta:
        managed = False
        db_table = 'signals_filter_view'

    def __str__(self):
        """
        Copied from the Signal model
        """
        created_at = self.created_at
        field_timezone = timezone.get_current_timezone() if settings.USE_TZ else None
        if timezone.is_aware(created_at) and field_timezone:
            created_at = created_at.astimezone(field_timezone)
        elif timezone.is_aware(created_at):
            created_at = timezone.make_naive(created_at, utc)

        return f'{self.signal_id} - {self.status_state} - {self.location_buurt_code} - {created_at.isoformat()}'

    # No changes allowed! This is a model for a database view!
    def save(self, *args, **kwargs):
        raise NotImplementedError(f'{type(self)} interacts with a database view, therefore save is not implemented')

    def delete(self, *args, **kwargs):
        raise NotImplementedError(f'{type(self)} interacts with a database view, therefore delete is not implemented')
