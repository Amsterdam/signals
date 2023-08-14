# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.db import transaction
from django.utils import timezone
from django_fsm import TransitionNotAllowed
from rest_framework import serializers
from rest_framework.fields import BooleanField, CharField

from signals.apps.history.models import Log
from signals.apps.signals.models import Reporter, Signal


class SignalReporterSerializer(serializers.ModelSerializer):
    allows_contact = BooleanField(source='_signal.allows_contact', read_only=True)
    sharing_allowed = BooleanField(required=True)

    class Meta:
        model = Reporter
        fields = (
            'id',
            'email',
            'phone',
            'allows_contact',
            'sharing_allowed',
            'state',
            'email_verification_token_expires',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'email_verified',
            'allows_contact',
            'state',
            'email_verification_token_expires',
            'created_at',
            'updated_at',
        )

    def _verify_email(self, reporter: Reporter, signal: Signal) -> bool:
        try:
            reporter.verify_email()
            reporter.save()

            self._log_to_history(reporter, 'E-mail verificatie verzonden.', signal)
        except TransitionNotAllowed:
            return False

        return True

    def _cancel_previous_reporters(self, signal: Signal) -> None:
        for reporter in signal.reporters.all():
            if reporter.state not in (Reporter.REPORTER_STATE_APPROVED, Reporter.REPORTER_STATE_CANCELLED):
                reporter.cancel()
                reporter.save()

    def _log_to_history(self, reporter: Reporter, description: str, signal: Signal) -> None:
        reporter.history_log.create(
            action=Log.ACTION_UPDATE,
            created_by=self.context.get('request').user.username,
            created_at=timezone.now(),
            description=description,
            _signal=signal,
        )

    def to_representation(self, instance: Reporter) -> dict:
        serialized = super().to_representation(instance)

        user = self.context['request'].user if 'request' in self.context else None
        if not user or not user.has_perm('signals.sia_can_view_contact_details'):
            serialized['email'] = '*****' if serialized['email'] else ''
            serialized['phone'] = '*****' if serialized['phone'] else ''

        return serialized

    @transaction.atomic()
    def create(self, validated_data: dict) -> Reporter:
        signal_id = self.context['view'].kwargs.get('parent_lookup__signal_id')
        signal = Signal.objects.get(pk=signal_id)

        self._cancel_previous_reporters(signal)

        reporter = Reporter()
        reporter.email = validated_data.get('email')
        reporter.phone = validated_data.get('phone')
        reporter.sharing_allowed = validated_data.get('sharing_allowed')
        reporter._signal = signal
        reporter.save()

        # When there is an email address available it should be verified
        verify_email_successful = self._verify_email(reporter, signal)

        # When there is no email address available but the phone number has changed
        # we can transition to approved
        if not verify_email_successful:
            try:
                reporter.approve()
                reporter.save()

                if reporter._signal.reporter.phone != reporter.phone:
                    self._log_to_history(reporter, 'Telefoonnummer is gewijzigd.', signal)

                # This can happen when the e-mail address is removed or blanked
                if reporter._signal.reporter.email != reporter.email:
                    self._log_to_history(reporter, 'E-mailadres is gewijzigd.', signal)
            except TransitionNotAllowed:
                # If everything fails the change request is not valid and should be
                # cancelled
                reporter.cancel()
                reporter.save()

                self._log_to_history(
                    reporter,
                    'Verzoek tot wijzigen contactgegevens geannuleerd.',
                    signal
                )

        return reporter


class CancelSignalReporterSerializer(serializers.Serializer):
    reason = CharField(required=False)
