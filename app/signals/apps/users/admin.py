# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam
import csv

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.postgres.aggregates import StringAgg
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext as _

from signals.apps.history.services import HistoryLogService
from signals.apps.users.models import Profile

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name = _('Profile')
    verbose_name_plural = _('Profile')
    fk_name = 'user'


class SignalsUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'departments')
    inlines = (ProfileInline, )

    actions = ['download_csv']

    @admin.display(description='Afdeling(en)')
    def departments(self, obj):
        if obj.profile and obj.profile.departments.exists():
            return ', '.join(obj.profile.departments.values_list('code', flat=True).order_by('code'))
        return ''

    @admin.action(description='Download CSV')
    def download_csv(self, request, queryset):
        """Download CSV of user accounts."""
        # If we don't specify the fields, a new query will be executed to retrieve
        # the groups for each result when iterating below
        queryset = queryset.values(
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_staff',
            'is_superuser',
            'is_active',
        )
        queryset = queryset.annotate(
            group_names=StringAgg('groups__name', ', ', distinct=True),
            department_codes=StringAgg('profile__departments__code', ', ', distinct=True)
        )

        column_headers = [
            'Gebruikersnaam',
            'E-mailadres',
            'Voornaam',
            'Achternaam',
            'Groep',
            'Staf',
            'Superuser',
            'Actief',
            'Afdeling(en)',
        ]

        now = timezone.localtime(timezone.now())
        filename = 'gebruikers-rapport-sia-{}.csv'.format(now.strftime('%Y%m%d_%H%M'))

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)

        writer = csv.writer(response, delimiter=';', quotechar='"')
        writer.writerow(column_headers)

        def ja_nee(value):
            return 'Ja' if value else 'Nee'

        for user in queryset:
            writer.writerow([
                user['username'],
                user['email'],
                user['first_name'],
                user['last_name'],
                user['group_names'],
                ja_nee(user['is_staff']),
                ja_nee(user['is_superuser']),
                ja_nee(user['is_active']),
                user['department_codes'],
            ])

        self.message_user(request, 'Created summary CSV file: {}'.format(filename))
        return response

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        """
        On the save from the model also add a history log in the admin panel
        """
        # TODO:: This currently only saves the changes on the user object.
        # it does not log the users rights/group and related Profile changes
        obj.save()
        if change:  # only trigger when an object has been changed
            HistoryLogService.log_update(instance=obj, user=request.user)


admin.site.unregister(User)
admin.site.register(User, SignalsUserAdmin)
