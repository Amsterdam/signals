# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
"""
Extract neighborhood data for a given municipality from CBS data.

Note:
- Centraal Bureau voor de Statistiek (CBS) neighborhood and municipal map data
  must be present in the Signalen database.
- The Signalen instance that we run this script for must serve one municipality.
- AreaTypes will be added that have names `<municipal_code>-wijk` and
  `<municipal_code>-buurt`.
- The Dutch "buurt" and "wijk" both translate to neighborhood, but in the
  Netherlands "wijk" areas are larger and consist of "buurt" areas. We use the
  Dutch terms below - the use of CBS data makes this code specific to the
  Netherlands.
"""
from django.core.management import BaseCommand, CommandError
from django.db import transaction

from signals.apps.signals.models import Area, AreaType

REQUIRED_DATASETS = {
    # Dataset names must match those defined in signals.apps.dataset.sources.cbs
    'CBS_MUNICIPAL_BORDERS_DATASET': 'cbs-gemeente-2022',
    'CBS_WIJK_DATASET': 'cbs-wijk-2022',
    'CBS_BUURT_DATASET': 'cbs-buurt-2022',
}


class Command(BaseCommand):
    def _cbs_data_present(self):
        """
        We need the CBS data municipal borders and neighborhood borders
        """
        all_present = True
        for value in REQUIRED_DATASETS.values():
            if not AreaType.objects.filter(code=value).exists():
                all_present = False
                msg = f'Required area type {value} is not present in database!'
                self.stdout.write(msg)
                continue

            area_type = AreaType.objects.get(code=value)
            if not Area.objects.filter(_type=area_type).count():
                all_present = False
                msg = f'No area data associated with AreaType {value}!'
                self.stdout.write(msg)

        return all_present

    def _municipal_code_is_correct(self, municipal_code):
        """Municipal code must be present in CBS data"""
        # Assumes that required dataset (municipal borders) is present.
        area_type = AreaType.objects.get(code=REQUIRED_DATASETS['CBS_MUNICIPAL_BORDERS_DATASET'])
        return Area.objects.filter(_type=area_type, code=municipal_code).exists()

    def _derive_dataset_codes(self, municipal_code):
        """Newly created datasets will use names based on municipal code"""
        municipal_code = municipal_code.lower()
        return f'{municipal_code}-wijk', f'{municipal_code}-buurt'

    def _copy_areas_to_area_type(self, area_qs, to_area_type):
        """Create a copy of a number of areas to a different area type"""
        for area in area_qs:
            area._type = to_area_type
            area.id = None
            area.save()

    def add_arguments(self, parser):
        parser.add_argument('--municipal_code', type=str, default=None, help='Municipal code (CBS GM_CODE).')

    def handle(self, *args, **options):
        """
        Find neighborhoods in requested municipality store them as a dataset.

        Note: storing as a dataset in this context means that a we derive
        area type names for the neighborhoods in the municipality under
        consideration. We store a copy of all relevant neighborhoods (both the
        Dutch "wijk" and "buurt" types of neighborhood) associated with the
        newly created AreaTypes.
        """
        cbs_wijk_dataset = REQUIRED_DATASETS['CBS_WIJK_DATASET']
        cbs_buurt_dataset = REQUIRED_DATASETS['CBS_BUURT_DATASET']
        municipal_code = options['municipal_code']

        if not self._cbs_data_present():
            raise CommandError('Required datasets are not available, exiting!')
        if not self._municipal_code_is_correct(municipal_code):
            raise CommandError('Provided municipal code is not present in CBS data, exiting!')
        self.stdout.write('Required CBS data are available.')

        # Datatype for our newly loaded data, note we drop the old copy.
        wijk_dataset_code, buurt_dataset_code = self._derive_dataset_codes(municipal_code)
        wijk_area_type, _ = AreaType.objects.get_or_create(code=wijk_dataset_code, name=wijk_dataset_code)
        buurt_area_type, _ = AreaType.objects.get_or_create(code=buurt_dataset_code, name=buurt_dataset_code)

        with transaction.atomic():
            to_remove_w = Area.objects.filter(_type=wijk_area_type)
            to_remove_b = Area.objects.filter(_type=buurt_area_type)

            self.stdout.write(f'\nThere are {to_remove_w.count()} old (wijk) area instances to remove')
            self.stdout.write(f'There are {to_remove_b.count()} old (buurt) area instances to remove')

            to_remove_w.delete()
            to_remove_b.delete()

            # We duplicate the neighborhoods in the municipality we are interested in, we select the geometry for
            # the municipality and use it to find the neighborhoods ("wijk" and "buurt") we want to copy.
            municipality_area_type = AreaType.objects.get(code=REQUIRED_DATASETS['CBS_MUNICIPAL_BORDERS_DATASET'])
            municipality = Area.objects.get(_type=municipality_area_type, code=municipal_code)
            self.stdout.write(f'\nNeighborhoods for the municipality of "{municipality.name}" will be copied')

            to_copy_w = Area.objects.filter(_type__code=cbs_wijk_dataset, geometry__intersects=municipality.geometry)
            to_copy_b = Area.objects.filter(_type__code=cbs_buurt_dataset, geometry__intersects=municipality.geometry)

            self.stdout.write(f'There are {to_copy_w.count()} new "wijk" area instances to copy.')
            self.stdout.write(f'"Wijk" area instances will be copied to dataset/AreaType {wijk_area_type.name}.')
            self.stdout.write(f'There are {to_copy_b.count()} new "buurt area instances to copy.')
            self.stdout.write(f'"Buurt" area instances will be copied to dataset/AreaType {buurt_area_type.name}.')

            self._copy_areas_to_area_type(to_copy_w, wijk_area_type)
            self._copy_areas_to_area_type(to_copy_b, buurt_area_type)

            self.stdout.write('Done.')
