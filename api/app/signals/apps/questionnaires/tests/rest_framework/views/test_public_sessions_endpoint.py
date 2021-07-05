# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import os

from django.test import override_settings
from django.urls import include, path
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APITestCase

from signals.apps.api.routers import SignalsRouterVersion1
from signals.apps.api.views import PublicSignalViewSet
from signals.apps.questionnaires.factories import QuestionnaireFactory, SessionFactory
from signals.apps.questionnaires.models import Questionnaire
from signals.apps.questionnaires.tests.mixin import ValidateJsonSchemaMixin
from signals.apps.signals.factories import SignalFactory, StatusFactory
from signals.apps.signals.workflow import GEMELD, REACTIE_GEVRAAGD

THIS_DIR = os.path.dirname(__file__)


extra_router = SignalsRouterVersion1()
extra_router.register(r'public/signals', PublicSignalViewSet, basename='public-signals')


urlpatterns = [
    path('', include(('signals.apps.questionnaires.urls', 'signals.apps.questionnaires'), namespace='v1')),
]


class NameSpace:
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns + extra_router.urls


@override_settings(ROOT_URLCONF=test_urlconf)
class TestPublicSessionEndpoint(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/public/qa/sessions/'

    def setUp(self):
        self.questionnaire = QuestionnaireFactory.create()
        self.session = SessionFactory.create(questionnaire=self.questionnaire)

        self.detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../json_schema/public_get_session_detail.json')
        )

    def test_session_detail(self):
        response = self.client.get(f'{self.base_endpoint}{self.session.uuid}')
        self.assertEqual(response.status_code, 200)

        self.assertJsonSchema(self.detail_schema, response.json())

    def test_session_detail_gone(self):
        now = timezone.now()
        with freeze_time(now - timezone.timedelta(days=1)):
            session = SessionFactory.create(questionnaire=self.questionnaire,
                                            started_at=now - timezone.timedelta(hours=6))

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()['detail'], 'Expired!')

        now = timezone.now()
        with freeze_time(now - timezone.timedelta(days=1)):
            session = SessionFactory.create(questionnaire=self.questionnaire,
                                            submit_before=now-timezone.timedelta(hours=1))

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()['detail'], 'Expired!')

    def test_session_detail_frozen(self):
        session = SessionFactory.create(questionnaire=self.questionnaire, frozen=True)

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()['detail'], 'Already used!')

    def test_session_detail_reaction_requested(self):
        questionnaire = QuestionnaireFactory.create(flow=Questionnaire.REACTION_REQUEST)

        session = SessionFactory.create(questionnaire=questionnaire)

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['detail'], f'Session {session.uuid} is not associated with a Signal.')

        signal = SignalFactory.create(status__state=GEMELD)
        session._signal = signal
        session.save()

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['detail'], f'Session {session.uuid} is invalidated.')

        status = StatusFactory(state=REACTIE_GEVRAAGD, _signal=signal)
        signal.status = status
        signal.save()

        latest_session = SessionFactory.create(questionnaire=questionnaire, _signal=signal)

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['detail'], f'Session {session.uuid} is invalidated.')

        response = self.client.get(f'{self.base_endpoint}{latest_session.uuid}')
        self.assertEqual(response.status_code, 200)

    def test_session_list_not_found(self):
        response = self.client.get(f'{self.base_endpoint}')
        self.assertEqual(response.status_code, 404)

    def test_session_create_not_found(self):
        response = self.client.post(f'{self.base_endpoint}', data={})
        self.assertEqual(response.status_code, 404)

    def test_session_update_not_allowed(self):
        response = self.client.patch(f'{self.base_endpoint}{self.questionnaire.uuid}', data={})
        self.assertEqual(response.status_code, 405)

    def test_session_delete_not_allowed(self):
        response = self.client.delete(f'{self.base_endpoint}{self.questionnaire.uuid}')
        self.assertEqual(response.status_code, 405)
