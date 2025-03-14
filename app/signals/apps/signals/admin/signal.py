# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2023 Gemeente Amsterdam
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import transaction

from signals.apps.signals import workflow
from signals.apps.signals.models import Category, Status, Signal


class CreateReportForm(admin.helpers.ActionForm):
    new_category = forms.ModelChoiceField(
        queryset=Category.objects.filter(parent__isnull=False),
        label='Nieuwe categorie',
        empty_label='Selecteer een categorie',
        required=False
    )


class SignalAdmin(admin.ModelAdmin):
    """
    signals.Signal model admin, allows some maintenance tasks.
    """
    action_form = CreateReportForm
    fields = ('id', 'created_at', 'updated_at', 'get_status_display', 'get_category')
    list_display = ('id', 'created_at', 'updated_at', 'get_status_display', 'get_category')
    list_display_links = None  # change page not relevant
    ordering = ('-id',)
    list_per_page = 20
    list_select_related = True

    list_filter = ['created_at', 'status__state', 'category_assignment__category__name']
    search_fields = ['id__exact']  # we do not want to page through 400k or more signals

    # Add an action that frees signals stuck between SIA and CityControl. These
    # signals need to be in workflow.VERZONDEN state.
    actions = [
        'free_signals',
        'change_category',
        'change_status_reopened',
        'change_status_cancelled',
        'change_status_handled'
    ]

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

    @admin.action(description='Zet categorie op')
    def change_category(self, request, queryset):
        if not request.POST['new_category']:
            return self.message_user(request, 'Kies een nieuwe categorie.')

        new_category = Category.objects.get(id=request.POST['new_category'])

        for signal in queryset:
            Signal.actions.update_category_assignment({
                'category': new_category,
            }, signal)

        self.message_user(request, f'Categorieën zijn aangepast naar {new_category.name}.')

    @admin.action(description='Zet status op heropend')
    def change_status_handled(self, request, queryset):
        for signal in queryset:
            Signal.actions.update_status(
                data={'text': 'De melding is heropend.', 'state': workflow.HEROPEND},
                signal=signal
            )

        self.message_user(request, 'Statussen zijn aangepast naar heropend.')

    @admin.action(description='Zet status op afgehandeld')
    def change_status_handled(self, request, queryset):
        for signal in queryset:
            try:
                Signal.actions.update_status(
                    data={'text': 'De melding is afgehandeld.', 'state': workflow.AFGEHANDELD},
                    signal=signal
                )
            except ValidationError as e:
                return self.message_user(request, f'Fout bij het afhandelen van melding {signal.id}: {e}')

        self.message_user(request, 'Statussen zijn aangepast naar afgehandeld.')

    @admin.action(description='Zet status op geannuleerd')
    def change_status_cancelled(self, request, queryset):
        for signal in queryset:
            try:
                Signal.actions.update_status(
                    data={'text': 'In bulk geannuleerd.', 'state': workflow.GEANNULEERD},
                    signal=signal
                )
            except ValidationError as e:
                return self.message_user(request, f'Fout bij het annuleren van melding {signal.id}: {e}')

        self.message_user(request, 'Statussen zijn aangepast naar geannuleerd.')

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
