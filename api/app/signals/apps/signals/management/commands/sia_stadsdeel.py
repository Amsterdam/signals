# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from django.core.management import BaseCommand
from django.db.models import Q, QuerySet

from signals.apps.signals.models import Area, Signal
from signals.apps.signals.models.location import AREA_STADSDEEL_TRANSLATION


class Command(BaseCommand):
    _area_qs = None
    _area_stadsdeel_mapping = AREA_STADSDEEL_TRANSLATION

    def handle(self, *args, **options) -> None:
        self.stdout.write(f'Total Signals: {Signal.objects.all().count()}')
        self.stdout.write('--------------------------------------------------------------------------------')

        for area in self._get_area_qs():
            self.stdout.write(f'Checking Area "{area.name}" (stadsdeel "{self._area_stadsdeel_mapping[area.code]}")')

            qs = Signal.objects.filter(location__geometrie__within=area.geometry)
            correct_qs = qs.filter(Q(location__stadsdeel=self._area_stadsdeel_mapping[area.code]))
            incorrect_qs = qs.filter(~Q(location__stadsdeel=self._area_stadsdeel_mapping[area.code]))
            incorrect_stadsdelen = ', '.join([stadsdeel or 'None' for stadsdeel in incorrect_qs.distinct('location__stadsdeel').order_by('location__stadsdeel').values_list('location__stadsdeel', flat=True)])  # noqa

            self.stdout.write(f'* Total Signals: {qs.count()}')
            self.stdout.write(f'* Total Signals correct stadsdeel label: {correct_qs.count()}')
            self.stdout.write(f'* Total Signals incorrect stadsdeel label: {incorrect_qs.count()}')
            self.stdout.write(f'** Incorrect stadsdeel labels: {incorrect_stadsdelen}')
            self.stdout.write('--------------------------------------------------------------------------------')

        self.stdout.write('\nDone!')

    def _get_area_qs(self) -> QuerySet:
        if not self._area_qs:
            self._area_qs = Area.objects.filter(_type__code='sia-stadsdeel')
        return self._area_qs
