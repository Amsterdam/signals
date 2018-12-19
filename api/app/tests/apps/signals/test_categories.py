from rest_framework.test import APITestCase

from signals.apps.signals.models import SubCategory
from signals.apps.signals.utils import resolve_categories
from tests.apps.signals.factories import MainCategoryFactory, SubCategoryFactory


class TestResolveCategories(APITestCase):
    def setUp(self):
        self.main_category = MainCategoryFactory.create()
        self.sub_category = SubCategoryFactory.create()

    def test_main_category(self):
        path = '/signals/v1/public/terms/categories/{}'.format(self.main_category.slug)
        main_category, sub_category = resolve_categories(path=path)

        self.assertEqual(self.main_category.pk, main_category.pk)

    def test_sub_category(self):
        path = '/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(
            self.sub_category.main_category.slug,
            self.sub_category.slug,
        )
        main_category, sub_category = resolve_categories(path=path)

        self.assertEqual(self.sub_category.main_category.pk, main_category.pk)
        self.assertEqual(self.sub_category.pk, sub_category.pk)

    def test_does_not_exists_sub_category(self):
        path = '/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(
            'does_not',
            'exists',
        )

        with self.assertRaises(SubCategory.DoesNotExist):
            resolve_categories(path=path)
