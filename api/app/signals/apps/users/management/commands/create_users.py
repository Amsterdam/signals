import csv
import logging
import os
import random
import re
import string
from collections import Counter

from django.contrib.auth.models import Group, User
from django.core.management import BaseCommand, CommandError

from signals.apps.signals.models import Department

log = logging.getLogger(__name__)


def split_non_empty(s, delimiter):
    return list(filter(str.strip, s.split(delimiter)))


def make_random_password():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20))


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('csv_path', nargs='+', type=str)

    def handle(self, *args, **options):  # noqa: C901
        try:
            csv_path = options["csv_path"][0]
            print(f"Processing {csv_path}")
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

        expected_fields_name = {
            'inlog',
            'naam',
            'emailadres',
            'adw_account',
            'rol',
            'actief',
            'organisatie',
            'dienst'
        }

        email_valid = r'[^@]+@[^@]+\.[^@]+'

        rol_group = {
            'monitor': 'monitors',
            'behandelaar': 'behandelaars',
            'coordinator': 'coordinatoren'
        }

        supervisor_roles = {
            'regievoerder'
        }

        departments_map = {}
        for department in Department.objects.all():
            code = department.code.lower()
            name = department.name.lower()
            departments_map[code] = code
            departments_map[name] = code

        all_groups = {}
        for group in Group.objects.all():
            all_groups[group.name] = group

        inlog_counter = Counter()
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
                    stripped_field = field.strip().strip('"')
                    value = stripped_field if fields_name[i] == 'naam' else stripped_field.lower()
                    drow[fields_name[i]] = value

                inlog_counter[drow['inlog']] += 1
                if inlog_counter[drow['inlog']] > 1:
                    log.warning(f"Inlog {drow['inlog']} komt vaker voor in regel {row_number}")
                    continue

                if not re.match(email_valid, drow['emailadres']):
                    log.warning(f"Ongeldige e-mail {drow['emailadres']} in regel {row_number}")
                    continue

                if drow['organisatie'] != 'gemeente amsterdam' or not re.match(
                        r'[^@]+@amsterdam.nl$', drow['emailadres']):
                    log.warning(f"User e-mail {drow['emailadres']} in regel moet in datapunt IDP "
                                "worden aangemaakt")

                rol = drow['rol']
                group = rol_group.get(rol)
                if not group and rol not in supervisor_roles:
                    raise CommandError(f"Ongeldige rol {rol} in regel {row_number}")

                department = drow['dienst']
                if department and department not in departments_map:
                    raise CommandError(f"Ongeldige dienst {department} in regel {row_number}")
                rows_to_be_processed.append(drow)

        # Then process the updates
        for drow in rows_to_be_processed:
            email = drow['emailadres']
            rol = drow['rol']
            group = rol_group.get(rol)
            is_superuser = True if rol in supervisor_roles else False
            is_active = True if drow['actief'] == 'j' else False
            dienst = drow['dienst']
            names = drow['naam'].split(' ', 1)
            if len(names) == 2:
                (first_name, last_name) = names
            else:
                (first_name, last_name) = ('', names[0])
            if dienst:
                department = departments_map.get(dienst)
            else:
                department = None

            try:
                user = User.objects.get(username=email)
            except User.DoesNotExist:
                user = None
            if not user:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=make_random_password(),
                    is_active=is_active,
                    is_superuser=is_superuser)
            else:
                user.is_superuser = is_superuser
                user.is_active = is_active
                user.save()

            new_groups = set()
            if group:
                new_groups.add(group)
            if department:
                new_groups.add(f'dep_{department}')
            old_groups = set(user.groups.values_list('name', flat=True))

            # Delete old groups not in new groups
            for group in old_groups - new_groups:
                all_groups[group].user_set.remove(user)

            # Add new groups not in old groups
            for group in new_groups - old_groups:
                all_groups[group].user_set.add(user)
            log.info(f"Processed user {email}")
