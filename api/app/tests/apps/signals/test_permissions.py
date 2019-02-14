""" Tests permissions.py """

from django.contrib.auth.models import Permission
from django.test.testcases import TestCase

from signals.apps.signals.permissions import CategoryPermissions
from tests.apps.signals.factories import SubCategory, SubCategoryFactory


class TestPermissions(TestCase):
    categories = []

    def setUp(self):
        SubCategory.objects.all().delete()
        self.assertEquals(0, SubCategory.objects.count())
        self.categories = [SubCategoryFactory.create() for _ in range(10)]

    def test_create_category_permissions(self):
        before_cnt = Permission.objects.count()

        CategoryPermissions.create_for_all_categories()

        self.assertEquals(before_cnt + 10, Permission.objects.count())

        for category in self.categories:
            category.refresh_from_db()
            self.assertIsNotNone(category.permission)
            self.assertEquals("Category access - " + category.name, category.permission.name)
            self.assertEquals("category_access_" + str(category.id), category.permission.codename)

    def test_create_category_permissions_only_once(self):
        """ Make sure category permissions are only created once for a category """

        before_cnt = Permission.objects.count()
        for category in self.categories[:4]:
            CategoryPermissions.create_for_category(category)

        self.assertEquals(before_cnt + 4, Permission.objects.count())
        CategoryPermissions.create_for_all_categories()
        self.assertEquals(before_cnt + 10, Permission.objects.count())

        for category in self.categories:
            category.refresh_from_db()
            self.assertIsNotNone(category.permission)
            self.assertEquals("Category access - " + category.name, category.permission.name)
            self.assertEquals("category_access_" + str(category.id), category.permission.codename)
