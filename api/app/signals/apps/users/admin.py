import csv

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.http import HttpResponse
from django.utils import timezone

from signals.apps.signals.permissions import CategoryPermissions


class SignalsUserAdmin(UserAdmin):
    actions = ['download_csv']

    def download_csv(self, request, queryset):
        """Download CSV of user accounts."""
        column_headers = [
            'Gebruikersnaam',
            'Emailadres',
            'Voornaam',
            'Achternaam',
            'Groep',
            'Staf',
            'Superuser',
            'Actief',
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
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                ', '.join(
                    user.groups.values_list('name', flat=True)
                ),
                ja_nee(user.is_staff),
                ja_nee(user.is_superuser),
                ja_nee(user.is_active),
            ])

        self.message_user(request, 'Created summary CSV file: {}'.format(filename))
        return response

    def get_form(self, request, obj=None, **kwargs):
        """ Makes sure the category permissions are updated on user form load """
        CategoryPermissions.create_for_all_categories()
        return super().get_form(request, obj=obj, **kwargs)


class SignalsGroupAdmin(GroupAdmin):
    def get_form(self, request, obj=None, **kwargs):
        """ Makes sure the category permissions are updated on group form load """
        CategoryPermissions.create_for_all_categories()
        return super().get_form(request, obj=obj, **kwargs)


admin.site.unregister(User)
admin.site.register(User, SignalsUserAdmin)

admin.site.unregister(Group)
admin.site.register(Group, SignalsGroupAdmin)
