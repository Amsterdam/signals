# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Management command that moves the category "Put / Riolering verstopt" to the
"Schoon" main category.
"""
from django.core.management import BaseCommand
from django.db import transaction

from signals.apps.signals.models import Category, Department, ServiceLevelObjective, Signal

MESSAGE = 'Omdat er nieuwe categorieën zijn ingevoerd in SIA is deze melding overnieuw ingedeeld.'


class Command(BaseCommand):
    def _create_new_category_inactivate_old(self):
        with transaction.atomic():
            old_main_category = Category.objects.get(slug='wegen-verkeer-straatmeubilair', parent__isnull=True)
            old_category = Category.objects.get(slug='put-riolering-verstopt', parent_id=old_main_category.pk)

            new_main_category = Category.objects.get(slug='schoon', parent__isnull=True)
            new_category = Category.objects.create(name='putrioleringverstopt', parent=new_main_category)
            new_category.name = 'Put / riolering verstopt'
            new_category.handling = 'I5DMC'
            new_category.handling_message = 'Uw melding wordt ingepland: wij laten u binnen 5 werkdagen weten ' \
                                            'hoe en wanneer uw melding wordt afgehandeld. Dat doen we via e-mail.'

            responsible_departments = Department.objects.filter(code__in=['ASC', 'CCA', 'STW', ])
            new_category.departments.add(
                *responsible_departments, through_defaults={'is_responsible': True, 'can_view': True})
            new_category.save()

            ServiceLevelObjective.objects.create(category=new_category, n_days=5, use_calendar_days=False)

            old_category.is_active = False
            old_category.save()

        return old_category, new_category

    def _move_signals(self, old_category, new_category):
        signals = Signal.objects.filter(category_assignment__category_id=old_category.pk)
        self.stdout.write(f'Before move there are {signals.count()} signals in the old category')

        for signal in signals.iterator():
            Signal.actions.update_category_assignment({'category': new_category, 'text': MESSAGE}, signal)

        self.stdout.write(f'After move there are {signals.count()} signals in the old category')

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating new categories ...')
        old_category, new_category = self._create_new_category_inactivate_old()
        self.stdout.write(f'Created {new_category.slug} to replace {old_category.slug}.')

        self.stdout.write('Moving signals ...')
        self._move_signals(old_category, new_category)

        self.stdout.write('Done!')
