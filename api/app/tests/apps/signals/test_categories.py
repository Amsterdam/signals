from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from signals.apps.signals.models import SubCategory
from signals.apps.signals.utils import resolve_categories
from tests.apps.signals.factories import MainCategoryFactory, SubCategoryFactory


class TestResolveCategories(APITestCase):
    def setUp(self):
        self.main_category = MainCategoryFactory.create()
        self.sub_category = SubCategoryFactory.create()

    def test_main_category(self):
        path = reverse('v1:category-detail', kwargs={'slug': self.main_category.slug})
        main_category, sub_category = resolve_categories(path=path)

        self.assertEqual(self.main_category.pk, main_category.pk)
        self.assertEqual(sub_category, None)

    def test_sub_category(self):
        path = reverse('v1:sub-category-detail', kwargs={
            'slug': self.sub_category.main_category.slug,
            'sub_slug': self.sub_category.slug
        })
        main_category, sub_category = resolve_categories(path=path)

        self.assertEqual(self.sub_category.main_category.pk, main_category.pk)
        self.assertEqual(self.sub_category.pk, sub_category.pk)

    def test_does_not_exists_sub_category(self):
        path = reverse('v1:sub-category-detail', kwargs={
            'slug': 'does_not',
            'sub_slug': 'exists'
        })

        with self.assertRaises(SubCategory.DoesNotExist):
            resolve_categories(path=path)
