from unittest import skip
from unittest.mock import patch

from django.http import Http404
from rest_framework.exceptions import APIException

from signals.apps.signals.models import Category
from signals.apps.signals.models.category_translation import CategoryTranslation
from tests.apps.signals.factories import CategoryFactory
from tests.test import SignalsBaseApiTestCase


class TestMlPredictCategory(SignalsBaseApiTestCase):
    test_host = 'http://testserver'
    endpoint = '/signals/v1/public/category/prediction'

    def setUp(self):
        self.test_parentcategory_overig = Category.objects.get(
            slug='overig',
            parent__isnull=True,
        )
        self.test_subcategory_overig = Category.objects.get(
            parent=self.test_parentcategory_overig,
            slug='overig',
            parent__isnull=False,
        )
        self.link_test_subcategory_overig = '/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(  # noqa
            self.test_host,
            self.test_subcategory_overig.parent.slug,
            self.test_subcategory_overig.slug,
        )

        self.test_subcategory = CategoryFactory.create()
        self.link_test_subcategory = '{}/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(  # noqa
            self.test_host,
            self.test_subcategory.parent.slug,
            self.test_subcategory.slug,
        )

        self.test_subcategory_translated = CategoryFactory.create()
        self.link_test_subcategory_translated = '{}/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(  # noqa
            self.test_host,
            self.test_subcategory_translated.parent.slug,
            self.test_subcategory_translated.slug,
        )

        self.link_test_subcategory_translation = CategoryTranslation.objects.create(
            old_category=self.test_subcategory_translated,
            new_category=self.test_subcategory,
            text='For testing purposes we translate this category',
            created_by='someone@example.com',
        )

    @skip('V1 Disabled')
    @patch('signals.apps.api.v1.public.views.MLPredictCategoryView._ml_predict')
    def test_predict(self, patched):
        patched.return_value = self.link_test_subcategory

        data = {'text': 'Give me the subcategory'}
        response = self.client.get(self.endpoint, data=data, format='json')

        self.assertEqual(response.status_code, 200)

        response_json = response.json()

        self.assertEqual(response_json['_links']['self']['href'], self.link_test_subcategory)

    @skip('V1 Disabled')
    @patch('signals.apps.api.v1.public.views.MLPredictCategoryView._ml_predict')
    def test_predict_translated(self, patched):
        patched.return_value = self.link_test_subcategory_translated

        data = {'text': 'Give me the subcategory, because of translations'}
        response = self.client.get(self.endpoint, data=data, format='json')

        self.assertEqual(response.status_code, 200)

        response_json = response.json()

        # This should be the translated category URL
        self.assertEqual(response_json['_links']['self']['href'], self.link_test_subcategory)

    @skip('V1 Disabled')
    @patch('signals.apps.api.v1.public.views.MLPredictCategoryView._ml_predict')
    def test_predict_overig(self, patched):
        patched.return_value = self.link_test_subcategory_overig

        data = {'text': 'deze test resulteert in de overige categorie'}
        response = self.client.get(self.endpoint, data=data, format='json')

        self.assertEqual(response.status_code, 200)

        response_json = response.json()

        self.assertEqual(response_json['_links']['self']['href'], self.link_test_subcategory_overig)

    @skip('V1 Disabled')
    @patch('signals.apps.api.v1.public.views.MLPredictCategoryView._ml_predict')
    def test_predict_overig_none(self, patched):
        patched.return_value = None

        data = {'text': 'deze test resulteert in de overige categorie'}
        response = self.client.get(self.endpoint, data=data, format='json')

        self.assertEqual(response.status_code, 200)

        response_json = response.json()

        self.assertEqual(response_json['_links']['self']['href'], self.link_test_subcategory_overig)

    @skip('V1 Disabled')
    @patch('signals.apps.api.v1.public.views.MLPredictCategoryView._ml_predict',
           side_effect=Http404)
    def test_predict_404(self, patched):
        data = {'text': '404'}
        response = self.client.get(self.endpoint, data=data, format='json')

        self.assertEqual(response.status_code, 404)

    @skip('V1 Disabled')
    @patch('signals.apps.api.v1.public.views.MLPredictCategoryView._ml_predict',
           side_effect=APIException)
    def test_predict_httpresponseservererror(self, patched):
        data = {'text': '500'}
        response = self.client.get(self.endpoint, data=data, format='json')

        self.assertEqual(response.status_code, 500)

    @skip('V1 Disabled')
    def test_predict_invalid_request(self):
        data = {}
        response = self.client.get(self.endpoint, data=data, format='json')

        self.assertEqual(response.status_code, 400)
