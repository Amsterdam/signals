# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
"""
Script to assign existing Signals to the areas specified by their AreaType.code
"""
from django.core.management import BaseCommand

from signals.apps.signals.models import Area, AreaType, Signal


class Command(BaseCommand):
    def add_arguments(self, parser):
        # For VNG installations 'district' is the AreaType.code that is used to
        # assign Signals to areas, hence the default.
        parser.add_argument(
            '--area_type_code', type=str, default='district', help='Area type code of areas to assign signals to.')

    def handle(self, *args, **options):
        area_type = AreaType.objects.get(code=options['area_type_code'])
        areas = Area.objects.filter(_type=area_type)
        n_assigned = 0
        n_unassigned = 0

        self.stdout.write(f'(Re-)assigning Signals to areas of {options["area_type_code"]} AreaType.')
        for signal in Signal.objects.all().select_related('location').iterator(chunk_size=2000):
            qs = areas.filter(geometry__contains=signal.location.geometrie)

            if qs.exists():
                area = qs.first()
                new_location = signal.location
                new_location.id = None

                new_location.area_type_code = area_type.code
                new_location.area_code = area.code
                new_location.area_name = area.name
                new_location.save()

                signal.location = new_location
                signal.save(update_fields=['location', 'updated_at'])

                n_assigned += 1
            else:
                n_unassigned += 1

        self.stdout.write(f'Updated area assignment for {n_assigned} Signals.')
        self.stdout.write(f'There are still {n_unassigned} Signals without a matching area.')
        self.stdout.write('Done!')
