# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import os

from django.core.management import call_command
from django.test import TestCase

from signals.apps.signals.models import Category

THIS_DIR = os.path.dirname(__file__)


class TestLoadCategories(TestCase):
    def test_load_categories(self):
        datafile = os.path.join(THIS_DIR, 'json_data', 'categories.json')
        datafile_update = os.path.join(THIS_DIR, 'json_data', 'categories-update.json')

        # load 'initial' categories
        call_command('load_categories', datafile)
        categories = Category.objects.filter(is_active=True)
        self.assertEqual(4, len(categories))
        # update categories, and make one inactive
        call_command('load_categories', datafile_update)
        categories = Category.objects.filter(is_active=True)
        self.assertEqual(3, len(categories))

        renamed = categories.get(slug='test-parent-cat1')
        self.assertEqual(renamed.description, 'renamed')

    def test_load_categories_with_existing_entries(self):
        main = Category.objects.create(**{
            "slug": "test-parent-cat1",
            "name": "test parent cat1",
            "handling": "REST",
            "is_active": True
        })

        # sub cat with same name as parent
        Category.objects.create(**{
            "slug": "test-parent-cat1",
            "name": "test parent cat1",
            "handling": "REST",
            "is_active": True,
            "parent": main
        })

        main2 = Category.objects.create(**{
            "slug": "test-parent-cat2",
            "name": "test parent cat2",
            "handling": "REST",
            "is_active": True
        })

        # sub cat with same name as parent, but different parent
        Category.objects.create(**{
            "slug": "test-parent-cat1",
            "name": "test parent cat1",
            "handling": "REST",
            "is_active": True,
            "parent": main2
        })

        datafile = os.path.join(THIS_DIR, 'json_data', 'categories.json')
        datafile_update = os.path.join(THIS_DIR, 'json_data', 'categories-update.json')

        # load 'initial' categories
        call_command('load_categories', datafile)
        categories = Category.objects.filter(is_active=True)
        self.assertEqual(4, len(categories))
        # update categories, and make one inactive
        call_command('load_categories', datafile_update)
        categories = Category.objects.filter(is_active=True)
        self.assertEqual(3, len(categories))

        renamed = categories.get(slug='test-parent-cat1')
        self.assertEqual(renamed.description, 'renamed')
