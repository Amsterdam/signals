import random
import string
from django.contrib.auth.models import Group, Permission, User
from django.core.management import BaseCommand

from signals.messaging.categories import ALL_DEPARTMENTS


def make_random_password():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20))


class Command(BaseCommand):

    def handle(self, *args, **options):
        monitors, created = Group.objects.get_or_create(name='monitors')
        behandelaars, created = Group.objects.get_or_create(name='behandelaars')
        coordinatoren, created = Group.objects.get_or_create(name='coordinatoren')

        add_status = Permission.objects.get(codename='add_status')
        add_category = Permission.objects.get(codename='add_category')

        behandelaars.permissions.add(add_status)
        coordinatoren.permissions.add(add_category)
        coordinatoren.permissions.add(add_status)

        all_departments = map(lambda x: 'dep_' + x.lower(), ALL_DEPARTMENTS.keys())
        for dep_name in all_departments:
            _, created = Group.objects.get_or_create(name=dep_name)

        # Add test users
        monitor = User.objects.get(username='signals.monitor@amsterdam.nl')
        if not monitor:
            monitor = User.objects.create_user(username='signals.monitor@amsterdam.nl',
                                            email='signals.monitor@amsterdam.nl',
                                            password=make_random_password())
            monitors.user_set.add(monitor)
        behandelaar = User.objects.get(username='signals.behandelaar@amsterdam.nl')
        if not behandelaar:
            behandelaar = User.objects.create_user(username='signals.behandelaar@amsterdam.nl',
                                            email='signals.behandelaar@amsterdam.nl',
                                            password=make_random_password())
            behandelaars.user_set.add(behandelaar)
        coordinator = User.objects.get(username='signals.coordinator@amsterdam.nl')
        if not coordinator:
            coordinator = User.objects.create_user(username='signals.coordinator@amsterdam.nl',
                                            email='signals.coordinator@amsterdam.nl',
                                            password=make_random_password())
            coordinatoren.user_set.add(coordinator)