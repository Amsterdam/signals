
from django.urls import NoReverseMatch
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.versioning import NamespaceVersioning

from signals.apps.signals.fields import MainCategoryHyperlinkedRelatedField
from signals.apps.signals.models import MainCategory


class TestMainCategoryHyperlinkedRelatedField(APITestCase):

    def test_category_detail_reverse(self):
        # We have namespaced URLs 
        with self.assertRaises(NoReverseMatch):
            reverse('category-detail')
        
        self.assertEqual(
            reverse('v1:category-detail', kwargs={'slug': 'afval'}),
            '/signals/v1/public/terms/categories/afval'
        )

    def test_main_category_hyperlinked_related_field_get_url(self):
        # We need a request with some extra properties set to be able to reverse
        # a namespaced URL.
        factory = APIRequestFactory()
        request = factory.get('/signals/signal/')
        request.version = 'v0'
        request.versioning_scheme = NamespaceVersioning()

        # See whether MainCategoryHyperlinkedRelatedField returns the correct URL 
        field = MainCategoryHyperlinkedRelatedField()

        url = field.get_url(
            obj=MainCategory.objects.get(slug='afval'),
            view_name='category-detail',
            request=request,
            format=None,
        )
        self.assertEqual(url, 'http://testserver/signals/v1/public/terms/categories/afval')

    def test_main_category_hyperlinked_related_field_to_internal_value(self):
        test_url = 'http://testserver/signals/v1/public/terms/categories/afval'

        factory = APIRequestFactory()
        request = factory.post('/signals/signal/', {'whatever': 'Does not matter!'})
        request.version = 'v0'
        request.versioning_scheme = NamespaceVersioning()

        field = MainCategoryHyperlinkedRelatedField()
        field._context = {'request': request}

        out = field.to_internal_value(test_url)
        self.assertIsInstance(out, MainCategory)
