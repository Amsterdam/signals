from unittest import mock
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError

from signals.apps.signals.factories import CategoryFactory
from signals.apps.signals.models import Category
from tests.test import SignalsBaseApiTestCase


class TestLegacyMlPredictCategory(SignalsBaseApiTestCase):
    test_host = 'http://testserver'
    endpoint = '/signals/category/prediction'

    def setUp(self):
        self.test_parentcategory_overig = Category.objects.get(slug='overig', parent__isnull=True)
        self.test_subcategory_overig = Category.objects.get(parent=self.test_parentcategory_overig, slug='overig',
                                                            parent__isnull=False)
        self.link_test_subcategory_overig = f'{self.test_host}/signals/v1/public/terms/categories/' \
                                            f'{self.test_subcategory_overig.parent.slug}/sub_categories/' \
                                            f'{self.test_subcategory_overig.slug,}'

        self.test_subcategory = CategoryFactory.create()
        self.link_test_subcategory = f'{self.test_host}/signals/v1/public/terms/categories/' \
                                     f'{self.test_subcategory.parent.slug}/sub_categories/{self.test_subcategory.slug}'

    @patch('signals.apps.api.v1.views.LegacyMlPredictCategoryView.ml_tool_client.predict')
    def test_predict(self, patched_ml_tool_client):
        response = mock.Mock()
        response.status_code = 200
        response.json = MagicMock(return_value={
            'hoofdrubriek': [[self.link_test_subcategory], [0.5]],
            'subrubriek': [[self.link_test_subcategory], [0.5]]
        })
        patched_ml_tool_client.return_value = response

        data = {'text': 'Give me the subcategory'}
        response = self.client.post(self.endpoint, data=data, format='json')

        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['subrubriek'][0][0], self.link_test_subcategory)

    @patch('signals.apps.api.v1.views.LegacyMlPredictCategoryView.ml_tool_client.predict',
           side_effect=ValidationError('error'))
    def test_predict_validation_error(self, *args):
        data = {'text': 'Give me the subcategory'}
        response = self.client.post(self.endpoint, data=data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()[0], 'error')
