# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2023 Gemeente Amsterdam
from django.contrib import admin
from django.db import transaction

from signals.apps.signals import workflow
from signals.apps.signals.models import Status


class SignalAdmin(admin.ModelAdmin):
    """
    signals.Signal model admin, allows some maintenance tasks.
    """
    fields = ('id', 'created_at', 'updated_at', 'get_status_display', 'get_category')
    list_display = ('id', 'created_at', 'updated_at', 'get_status_display', 'get_category')
    list_display_links = None  # change page not relevant
    ordering = ('-id',)
    list_per_page = 20
    list_select_related = True
    search_fields = ['id__exact']  # we do not want to page through 400k or more signals

    # Add an action that frees signals stuck between SIA and CityControl. These
    # signals need to be in workflow.VERZONDEN state.
    actions = ['free_signals']

    @admin.action(description='Free SIA signals (meldingen) stuck in state VERZONDEN.')
    def free_signals(self, request, queryset):
        filtered_signals = queryset.filter(status__state=workflow.VERZONDEN)

        with transaction.atomic():
            updated_signal_ids = []
            for signal in filtered_signals:
                new_status = Status(
                    _signal=signal,
                    state=workflow.AFGEHANDELD_EXTERN,
                    text='Vastgelopen melding vrijgegeven zonder tussenkomst CityControl.',
                    created_by=request.user.email
                )
                new_status.save()
                signal.status = new_status
                signal.save()
                updated_signal_ids.append(signal.id)

            if updated_signal_ids:
                msg = 'Successfully freed the following IDs: {}'.format(','.join(
                    str(_id) for _id in updated_signal_ids
                ))
            else:
                msg = 'No IDs were freed.'

            transaction.on_commit(lambda: self.message_user(request, msg))

    # Get the human-readable status and category:
    @admin.display(description='status')
    def get_status_display(self, obj):
        return obj.status.get_state_display()

    @admin.display(description='category')
    def get_category(self, obj):
        return obj.category_assignment.category.name

    # Disable editing on this model (change page customization)
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
