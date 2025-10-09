from django.test import TestCase
from import_export.formats.base_formats import JSON
from tablib import Dataset

from signals.apps.signals.factories import DepartmentFactory, CategoryFactory, QuestionFactory, ParentCategoryFactory, \
    ExpressionFactory, AreaFactory, RoutingExpressionFactory, AreaTypeFactory
from signals.apps.signals.factories.category_departments import CategoryDepartmentFactory
from signals.apps.signals.factories.category_question import CategoryQuestionFactory
from signals.apps.signals.models import Category, Question, Department, Expression, Area, RoutingExpression, AreaType
from signals.apps.signals.resources import CategoryResource, QuestionResource, DepartmentResource, ExpressionResource, \
    AreaResource, RoutingExpressionResource, AreaTypeResource
from signals.apps.users.factories import UserFactory


class CategoryImportExportTest(TestCase):
    def setUp(self):
        self.parent_category = ParentCategoryFactory.create()
        self.category = CategoryFactory.create(parent=self.parent_category)

    def test_category_export_json(self):
        resource = CategoryResource()
        dataset = resource.export([self.category], format=JSON())
        json_data = dataset.json

        self.assertIn(self.parent_category.slug, json_data)
        self.assertNotIn('"id":', json_data)
        self.assertNotIn('"departments":', json_data)
        self.assertNotIn('"questions":', json_data)
        self.assertNotIn('"questionnaire":', json_data)


    def test_category_import_json(self):
        resource = CategoryResource()

        # export to json
        export_category = resource.export([self.parent_category, self.category], format=JSON())
        json_data = export_category.json

        # import json
        import_dataset = Dataset().load(json_data, format="json")

        # dry run: should not have errors
        result = resource.import_data(import_dataset, dry_run=True)
        self.assertFalse(result.has_errors())

        # actual import
        resource.import_data(import_dataset, dry_run=False)

        # verify that category was imported correctly
        imported = Category.objects.get(name=self.category.name)
        self.assertEqual(imported.name, self.category.name)


class QuestionImportExportTest(TestCase):
    def setUp(self):
        self.category = CategoryFactory.create()
        self.question = QuestionFactory.create()
        self.category_question = CategoryQuestionFactory.create(category=self.category, question=self.question)

    def test_question_export_json(self):
        resource = QuestionResource()
        dataset = resource.export([self.question], format=JSON())
        json_data = dataset.json

        self.assertIn(self.question.key, json_data)
        self.assertIn(f"{self.category.slug}|{self.category_question.order}", json_data)
        self.assertNotIn('"id":', json_data)

    def test_question_import_json(self):
        resource = QuestionResource()

        # export to json
        export_question = resource.export([self.question], format=JSON())
        json_data = export_question.json

        # import json
        import_dataset = Dataset().load(json_data, format="json")

        # dry run: should not have errors
        result = resource.import_data(import_dataset, dry_run=True)
        self.assertFalse(result.has_errors())

        # actual import
        resource.import_data(import_dataset, dry_run=False)

        # verify that question was imported correctly
        imported = Question.objects.get(key=self.question.key)
        self.assertEqual(imported.key, self.question.key)
        self.assertEqual(imported.categoryquestion_set.first().category, self.category)
        self.assertEqual(imported.categoryquestion_set.first().question, self.question)
        self.assertEqual(imported.categoryquestion_set.first().order, self.category_question.order)


class DepartmentImportExportTest(TestCase):
    def setUp(self):
        self.category = CategoryFactory.create()
        self.department = DepartmentFactory.create()
        self.category_department = CategoryDepartmentFactory.create(category=self.category, department=self.department)

    def test_department_export_json(self):
        resource = DepartmentResource()
        dataset = resource.export([self.department], format=JSON())
        json_data = dataset.json

        self.assertIn(self.department.code, json_data)
        self.assertIn(f"{self.category.slug}|{self.category_department.is_responsible}|{self.category_department.can_view}", json_data)
        self.assertNotIn('"id":', json_data)

    def test_department_import_json(self):
        resource = DepartmentResource()

        # export to json
        export_department = resource.export([self.department], format=JSON())
        json_data = export_department.json

        # import json
        import_dataset = Dataset().load(json_data, format="json")

        # dry run: should not have errors
        result = resource.import_data(import_dataset, dry_run=True)
        self.assertFalse(result.has_errors())

        # actual import
        resource.import_data(import_dataset, dry_run=False)

        # verify that department was imported correctly
        imported = Department.objects.get(code=self.department.code)
        self.assertEqual(imported.code, self.department.code)
        self.assertEqual(imported.categorydepartment_set.first().category, self.category)
        self.assertEqual(imported.categorydepartment_set.first().department, self.department)
        self.assertEqual(imported.categorydepartment_set.first().is_responsible, self.category_department.is_responsible)
        self.assertEqual(imported.categorydepartment_set.first().can_view, self.category_department.can_view)


class ExpressionImportExportTest(TestCase):
    def setUp(self):
        self.expression = ExpressionFactory.create()

    def test_expression_export_json(self):
        resource = ExpressionResource()
        dataset = resource.export([self.expression], format=JSON())
        json_data = dataset.json

        self.assertIn(self.expression.code, json_data)
        self.assertIn(self.expression._type.name, json_data)
        self.assertNotIn('"id":', json_data)

    def test_expression_import_json(self):
        resource = ExpressionResource()

        # export to json
        export_expression = resource.export([self.expression], format=JSON())
        json_data = export_expression.json

        # import json
        import_dataset = Dataset().load(json_data, format="json")

        # dry run: should not have errors
        result = resource.import_data(import_dataset, dry_run=True)
        self.assertFalse(result.has_errors())

        # actual import
        resource.import_data(import_dataset, dry_run=False)

        # verify that expression was imported correctly
        imported = Expression.objects.get(code=self.expression.code)
        self.assertEqual(imported.code, self.expression.code)


class AreaImportExportTest(TestCase):
    def setUp(self):
        self.area = AreaFactory.create()

    def test_area_export_json(self):
        resource = AreaResource()
        dataset = resource.export([self.area], format=JSON())
        json_data = dataset.json

        self.assertIn(self.area.code, json_data)
        self.assertIn(self.area._type.code, json_data)
        self.assertNotIn('"id":', json_data)

    def test_area_import_json(self):
        resource = AreaResource()

        # export to json
        export_area = resource.export([self.area], format=JSON())
        json_data = export_area.json

        # import json
        import_dataset = Dataset().load(json_data, format="json")

        # dry run: should not have errors
        result = resource.import_data(import_dataset, dry_run=True)
        self.assertFalse(result.has_errors())

        # actual import
        resource.import_data(import_dataset, dry_run=False)

        # verify that area was imported correctly
        imported = Area.objects.get(code=self.area.code)
        self.assertEqual(imported.code, self.area.code)


class RoutingExpressionImportExportTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.department = DepartmentFactory.create()
        self.expression = ExpressionFactory.create()
        self.user.profile.departments.add(self.department)
        self.routing_expression = RoutingExpressionFactory.create(
            _user=self.user,
            _department=self.department,
            _expression=self.expression
        )

    def test_routing_expression_export_json(self):
        resource = RoutingExpressionResource()
        dataset = resource.export([self.routing_expression], format=JSON())
        json_data = dataset.json

        self.assertIn(self.user.username, json_data)
        self.assertIn(self.department.code, json_data)
        self.assertIn(self.expression.name, json_data)
        self.assertNotIn('"id":', json_data)

    def test_routing_expression_import_json(self):
        resource = RoutingExpressionResource()

        # export to json
        export_routing_expression = resource.export([self.routing_expression], format=JSON())
        json_data = export_routing_expression.json

        # import json
        import_dataset = Dataset().load(json_data, format="json")

        # dry run: should not have errors
        result = resource.import_data(import_dataset, dry_run=True)
        self.assertFalse(result.has_errors())

        # actual import
        resource.import_data(import_dataset, dry_run=False)

        # verify that routing_expression was imported correctly
        imported = RoutingExpression.objects.get(pk=self.routing_expression.id)
        self.assertEqual(imported._expression, self.expression)
        self.assertEqual(imported._user, self.user)
        self.assertEqual(imported._department, self.department)


class AreaTypeImportExportTest(TestCase):
    def setUp(self):
        self.area_type = AreaTypeFactory.create()

    def test_area_type_export_json(self):
        resource = AreaTypeResource()
        dataset = resource.export([self.area_type], format=JSON())
        json_data = dataset.json

        self.assertIn(self.area_type.code, json_data)
        self.assertNotIn('"id":', json_data)

    def test_area_type_import_json(self):
        resource = AreaTypeResource()

        # export to json
        export_area_type = resource.export([self.area_type], format=JSON())
        json_data = export_area_type.json

        # import json
        import_dataset = Dataset().load(json_data, format="json")

        # dry run: should not have errors
        result = resource.import_data(import_dataset, dry_run=True)
        self.assertFalse(result.has_errors())

        # actual import
        resource.import_data(import_dataset, dry_run=False)

        # verify that area_type was imported correctly
        imported = AreaType.objects.get(code=self.area_type.code)
        self.assertEqual(imported.code, self.area_type.code)