# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Gemeente Amsterdam
import importlib

from django.contrib import admin
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import include, path, resolve

from signals.apps.classification.models import TrainingSet
from signals.apps.classification.models.classifier import Classifier


class _NameSpace:
    urlpatterns: list


_urlconf_with_classification = _NameSpace()
_urlconf_with_classification.urlpatterns = [
    path('', include('signals.apps.classification.urls')),
]


class TestClassificationUrlFeatureFlag(TestCase):
    def test_endpoint_returns_404_when_flag_off(self):
        # The test environment runs with CLASSIFICATION_ENABLED unset (False),
        # so the classification URL include is not mounted in api.urls.
        response = self.client.post(
            '/signals/category/prediction', data={'text': 'foo'}, content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    @override_settings(ROOT_URLCONF=_urlconf_with_classification)
    def test_endpoint_routable_when_flag_on(self):
        # Simulates the flag-on state by directly mounting classification.urls as the ROOT_URLCONF.
        # We only assert the URL resolves to the correct route name; the view itself has heavy init
        # (nltk download, DB lookups) which isn't what this test is covering.
        match = resolve('/category/prediction')
        self.assertEqual(match.view_name, 'ml-tool-predict-proxy')


class TestClassificationAdminFeatureFlag(TestCase):
    def test_admin_not_registered_when_flag_off(self):
        # Flag is off in the test environment; Django autodiscover ran with the flag off
        # so the classification admin registrations should not be present.
        self.assertFalse(admin.site.is_registered(TrainingSet))
        self.assertFalse(admin.site.is_registered(Classifier))

    def test_admin_registered_when_flag_on(self):
        self.addCleanup(
            lambda: admin.site.is_registered(TrainingSet) and admin.site.unregister(TrainingSet)
        )
        self.addCleanup(
            lambda: admin.site.is_registered(Classifier) and admin.site.unregister(Classifier)
        )

        from signals.apps.classification import admin as classification_admin

        with override_settings(FEATURE_FLAGS={'CLASSIFICATION_ENABLED': True}):
            importlib.reload(classification_admin)
            self.assertTrue(admin.site.is_registered(TrainingSet))
            self.assertTrue(admin.site.is_registered(Classifier))


class TestTrainMlCommandFeatureFlag(TestCase):
    def test_command_raises_when_flag_off(self):
        with self.assertRaises(CommandError):
            call_command('train-ml', 1)
