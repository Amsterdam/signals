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
        self.assertEqual(renamed.name, 'test parent cat1 (renamed)')
