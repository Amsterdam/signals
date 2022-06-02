# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from django.conf import settings

from signals.apps.history.models import Log


class SignalLogService:
    @staticmethod
    def log_create_initial(signal):
        if not settings.FEATURE_FLAGS.get('SIGNAL_HISTORY_LOG_ENABLED', False):
            return

        if signal.is_child:
            # We cannot create a GenericRelation on the Signal model because the naming will clash with the ForeignKey
            # `_signal` defined on the Log model. So for now Log rules for a specific Signal are created as seen here:
            Log.objects.create(
                action=Log.ACTION_CREATE,
                extra=signal.id,
                object=signal,
                created_by=None,
                created_at=signal.created_at,
                _signal=signal.parent,
            )

        SignalLogService.log_update_location(signal.location)
        SignalLogService.log_update_status(signal.status)
        SignalLogService.log_update_category_assignment(signal.category_assignment)
        SignalLogService.log_update_priority(signal.priority)
        SignalLogService.log_update_type(signal.type_assignment)

    @staticmethod
    def log_create_note(note):
        if not settings.FEATURE_FLAGS.get('SIGNAL_HISTORY_LOG_ENABLED', False):
            return

        note.history_log.create(
            action=Log.ACTION_UPDATE,
            description=note.text,
            extra='Notitie toegevoegd',
            created_by=note.created_by,
            created_at=note.created_at,
            _signal=note._signal,
        )

    @staticmethod
    def log_update_category_assignment(category_assignment):
        if not settings.FEATURE_FLAGS.get('SIGNAL_HISTORY_LOG_ENABLED', False):
            return

        if category_assignment.category.slo.exists():
            category_assignment.category.slo.first().history_log.create(
                action=Log.ACTION_UPDATE,
                description=category_assignment.category.handling_message,
                created_by=category_assignment.created_by,
                created_at=category_assignment.created_at,
                _signal=category_assignment._signal,
            )

        category_assignment.history_log.create(
            action=Log.ACTION_UPDATE,
            extra=category_assignment.category.name,
            created_by=category_assignment.created_by,
            created_at=category_assignment.created_at,
            _signal=category_assignment._signal,
        )

    @staticmethod
    def log_update_location(location):
        if not settings.FEATURE_FLAGS.get('SIGNAL_HISTORY_LOG_ENABLED', False):
            return

        location.history_log.create(
            action=Log.ACTION_UPDATE,
            extra='Locatie gewijzigd',
            created_by=location.created_by,
            created_at=location.created_at,
            _signal=location._signal,
        )

    @staticmethod
    def log_update_priority(priority):
        if not settings.FEATURE_FLAGS.get('SIGNAL_HISTORY_LOG_ENABLED', False):
            return

        priority.history_log.create(
            action=Log.ACTION_UPDATE,
            extra=priority.priority,
            created_by=priority.created_by,
            created_at=priority.created_at,
            _signal=priority._signal,
        )

    @staticmethod
    def log_update_status(status):
        if not settings.FEATURE_FLAGS.get('SIGNAL_HISTORY_LOG_ENABLED', False):
            return

        status.history_log.create(
            action=Log.ACTION_UPDATE,
            description=status.text,
            extra=status.state,
            created_by=status.created_by,
            created_at=status.created_at,
            _signal=status._signal,
        )

    @staticmethod
    def log_update_type(_type):
        if not settings.FEATURE_FLAGS.get('SIGNAL_HISTORY_LOG_ENABLED', False):
            return

        _type.history_log.create(
            action=Log.ACTION_UPDATE,
            extra=_type.name,
            created_by=_type.created_by,
            created_at=_type.created_at,
            _signal=_type._signal,
        )

    @staticmethod
    def log_update_user_assignment(user_assignment):
        if not settings.FEATURE_FLAGS.get('SIGNAL_HISTORY_LOG_ENABLED', False):
            return

        log_extra = user_assignment.user.email if user_assignment.user else None
        user_assignment.history_log.create(
            action=Log.ACTION_UPDATE,
            extra=log_extra,
            created_by=user_assignment.created_by,
            created_at=user_assignment.created_at,
            _signal=user_assignment._signal,
        )

    @staticmethod
    def log_update_signal_departments(signal_departments):
        if not settings.FEATURE_FLAGS.get('SIGNAL_HISTORY_LOG_ENABLED', False):
            return

        log_description = ', '.join(signal_departments.departments.values_list('code', flat=True))
        signal_departments.history_log.create(
            action=Log.ACTION_UPDATE,
            description=log_description,
            created_by=signal_departments.created_by,
            created_at=signal_departments.created_at,
            _signal=signal_departments._signal,
        )
