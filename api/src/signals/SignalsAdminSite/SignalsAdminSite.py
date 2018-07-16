# from django.contrib import admin
from django.contrib.admin import AdminSite
# from django.contrib.auth.admin import UserAdmin
# from signals.models import SignalsUser


class SignalsAdminSite(AdminSite):
    site_header = 'Signals administration'


admin_site = SignalsAdminSite(name='signals_admin')

# admin_site.register(SignalsUser, UserAdmin)