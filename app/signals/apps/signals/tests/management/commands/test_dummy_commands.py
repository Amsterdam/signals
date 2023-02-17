# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from io import StringIO

from django.core.management import call_command
from django.test import TransactionTestCase

from signals.apps.signals.factories import CategoryFactory, ParentCategoryFactory
from signals.apps.signals.models import Category, Department, Signal, Source


class TestDummyCategoriesCommand(TransactionTestCase):
    def test_command(self):
        parent_db_cnt = Category.objects.filter(parent__isnull=True).count()
        child_db_cnt = Category.objects.filter(parent__isnull=False).count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_categories', stdout=out, stderr=err)
        self.assertEqual(Category.objects.filter(parent__isnull=True).count(), parent_db_cnt + 1)
        self.assertEqual(Category.objects.filter(parent__isnull=False).count(), child_db_cnt + 1)

    def test_command_with_parents_to_create_parameter(self):
        parent_db_cnt = Category.objects.filter(parent__isnull=True).count()
        child_db_cnt = Category.objects.filter(parent__isnull=False).count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_categories', parents_to_create=5, stdout=out, stderr=err)
        self.assertEqual(Category.objects.filter(parent__isnull=True).count(), parent_db_cnt + 5)
        self.assertEqual(Category.objects.filter(parent__isnull=False).count(), child_db_cnt + 5)

    def test_command_with_children_to_create_parameter(self):
        parent_db_cnt = Category.objects.filter(parent__isnull=True).count()
        child_db_cnt = Category.objects.filter(parent__isnull=False).count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_categories', children_to_create=5, stdout=out, stderr=err)
        self.assertEqual(Category.objects.filter(parent__isnull=True).count(), parent_db_cnt + 1)
        self.assertEqual(Category.objects.filter(parent__isnull=False).count(), child_db_cnt + 5)

    def test_command_with_parent_slug_children_to_create_parameter(self):
        parent_category = ParentCategoryFactory.create(slug='wonen')

        parent_db_cnt = Category.objects.filter(parent__isnull=True).count()
        child_db_cnt = Category.objects.filter(parent__isnull=False).count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_categories', parent_slug=parent_category.slug, children_to_create=5, stdout=out, stderr=err)

        self.assertEqual(Category.objects.filter(parent__isnull=True).count(), parent_db_cnt)
        self.assertEqual(Category.objects.filter(parent__isnull=False).count(), child_db_cnt + 5)

    def test_command_with_invalid_parameters(self):
        parent_db_cnt = Category.objects.filter(parent__isnull=True).count()
        child_db_cnt = Category.objects.filter(parent__isnull=False).count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_categories', parents_to_create=-1, stdout=out, stderr=err)
        self.assertEqual(Category.objects.filter(parent__isnull=True).count(), parent_db_cnt)

        call_command('dummy_categories', parents_to_create=10000000000, stdout=out, stderr=err)
        self.assertEqual(Category.objects.filter(parent__isnull=True).count(), parent_db_cnt)

        call_command('dummy_categories', children_to_create=-1, stdout=out, stderr=err)
        self.assertEqual(Category.objects.filter(parent__isnull=False).count(), child_db_cnt)

        call_command('dummy_categories', children_to_create=10000000000, stdout=out, stderr=err)
        self.assertEqual(Category.objects.filter(parent__isnull=False).count(), child_db_cnt)


class TestDummyDepartmentCommand(TransactionTestCase):
    def test_command(self):
        db_cnt = Department.objects.count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_departments', stdout=out, stderr=err)
        self.assertEqual(Department.objects.count(), db_cnt + 1)

    def test_command_with_parameters(self):
        db_cnt = Department.objects.count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_departments', to_create=5, stdout=out, stderr=err)
        self.assertEqual(Department.objects.count(), db_cnt + 5)

    def test_command_with_invalid_parameters(self):
        db_cnt = Department.objects.count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_departments', to_create=-1, stdout=out, stderr=err)
        self.assertEqual(Department.objects.count(), db_cnt)

        call_command('dummy_departments', to_create=10000000000, stdout=out, stderr=err)
        self.assertEqual(Department.objects.count(), db_cnt)


class TestDummySourceCommand(TransactionTestCase):
    def test_command(self):
        db_cnt = Source.objects.count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_sources', stdout=out, stderr=err)
        self.assertEqual(Source.objects.count(), db_cnt + 1)

    def test_command_with_parameters(self):
        db_cnt = Source.objects.count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_sources', to_create=5, stdout=out, stderr=err)
        self.assertEqual(Source.objects.count(), db_cnt + 5)

    def test_command_with_invalid_parameters(self):
        db_cnt = Source.objects.count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_sources', to_create=-1, stdout=out, stderr=err)
        self.assertEqual(Source.objects.count(), db_cnt)

        call_command('dummy_sources', to_create=10000000000, stdout=out, stderr=err)
        self.assertEqual(Source.objects.count(), db_cnt)


class TestDummySignalsCommand(TransactionTestCase):
    def test_command(self):
        CategoryFactory.create()

        db_cnt = Signal.objects.count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_signals', stdout=out, stderr=err)
        self.assertEqual(Signal.objects.count(), db_cnt + 100)

    def test_command_with_parameters(self):
        CategoryFactory.create()

        db_cnt = Signal.objects.count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_signals', to_create=5, stdout=out, stderr=err)
        self.assertEqual(Signal.objects.count(), db_cnt + 5)

    def test_command_with_invalid_parameters(self):
        CategoryFactory.create()

        db_cnt = Signal.objects.count()

        out = StringIO()
        err = StringIO()

        call_command('dummy_signals', to_create=-1, stdout=out, stderr=err)
        self.assertEqual(Signal.objects.count(), db_cnt)

        call_command('dummy_signals', to_create=10000000000, stdout=out, stderr=err)
        self.assertEqual(Signal.objects.count(), db_cnt)
