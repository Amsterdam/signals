import csv
import django
import os
import logging
import random
import re
import string
from django.contrib.auth.models import Group, User
from django.core.management import BaseCommand, CommandError
from signals.messaging.categories import ALL_DEPARTMENTS

log = logging.getLogger(__name__)


def split_non_empty(s, delimiter):
    return list(filter(str.strip, s.split(delimiter)))

def make_random_password():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20))


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('csv_path', nargs='+', type=str)

    def handle(self, *args, **options):
        try:
            # your logic here
            csv_path = options["csv_path"][0]
            print(csv_path)
        except Exception as e:
            CommandError(repr(e))

        # args = 'Users.csv'
        # help1 = 'Import `Users`.csv into `Users` database. '

        # if len(args) != 1:
        #     raise CommandError("Invalid Invocation. See help.")
        #
        # csv_path = args[0]
        if not os.path.exists(csv_path):
            raise CommandError(f"{csv_path} doesnt exist.")

        expected_fields_name = {'user_email', 'groups', 'departments', 'superuser', 'staff', 'action'}

        email_valid = r'[^@]+@[^@]+\.[^@]+'
        allowed_groups = {'monitors', 'behandelaars', 'coordinatoren'}
        allowed_departments = set(map(lambda x: x.lower(), ALL_DEPARTMENTS.keys()))

        all_groups = {}
        for group in Group.objects.all():
            all_groups[group.name] = group

        rows_to_be_processed = []
        with open(csv_path, 'rt') as csvFile:
            reader = csv.reader(csvFile, delimiter=',', quotechar="\"")
            row_number = 0
            for row in reader:
                row_number += 1
                if row_number == 1:
                    fields_name = row
                    for i, _ in enumerate(fields_name):
                        fields_name[i] = fields_name[i].strip().strip('"').lower()
                        fields_name[i] = fields_name[i].replace(' ', '_')
                        if not fields_name[i] in expected_fields_name:
                            raise CommandError("%s field is not expected" % (fields_name[i]))
                    continue

                # Read all rows and check contents
                drow = {}
                for i, field in enumerate(row):
                    drow[fields_name[i]] = field.strip().strip('"').lower()

                if not re.match(email_valid, drow['user_email']):
                    raise CommandError(f"Invalid e-mail {drow['user_email']} in row {row_number}")

                for group in split_non_empty(drow['groups'], ';'):
                    if group not in allowed_groups:
                        raise CommandError(f"Invalid group {group} in row {row_number}")

                for department in split_non_empty(drow['departments'], ';'):
                    if department not in allowed_departments:
                        raise CommandError(f"Invalid department {department} in row {row_number}")
                rows_to_be_processed.append(drow)

        # Then process the updates
        for drow in rows_to_be_processed:
            try:
                user = User.objects.get(username=drow['user_email'])
            except User.DoesNotExist:
                user = None
            if drow['action'] == 'delete':
                if user:
                    user.delete()

            else:
                if not user:
                    user = User.objects.create_user(
                        username=drow['user_email'],
                        email=drow['user_email'],
                        password=make_random_password(),
                        is_superuser=(drow['superuser'] == 'true'),
                        is_staff=(drow['staff'] == 'true')
                    )
                else:
                    user.is_superuser = drow['superuser'] == 'true'
                    user.is_staff = drow['staff'] == 'true'
                    user.save()

                new_groups = set(split_non_empty(drow['groups'],';'))
                new_groups |= set(map(lambda d: 'dep_' + d, split_non_empty(drow['departments'],';')))
                old_groups = set(user.groups.values_list('name', flat=True))

                # Delete old groups not in new groups
                for group in old_groups - new_groups:
                    all_groups[group].user_set.remove(user)

                # Add new groups not in old groups
                for group in new_groups - old_groups:
                    all_groups[group].user_set.add(user)

            log.info(f"Processed user {drow['user_email']}")
