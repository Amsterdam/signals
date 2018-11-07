from unittest import expectedFailure

from django.test import TestCase, override_settings
from zds_client.client import ClientError

from signals.apps.zds.exceptions import CaseNotCreatedException
from signals.apps.zds.tasks import (
    add_document_to_case,
    add_status_to_case,
    connect_signal_to_case,
    create_case,
    create_document
)
from tests.apps.signals.factories import SignalFactory, SignalFactoryWithImage
from tests.apps.zds.factories import ZaakSignalFactory


class TestTasks(TestCase):

    @expectedFailure
    def test_create_case_no_case(self):
        # This test will only pass once it is connected to the staging database.
        signal = SignalFactory()
        signal = create_case(signal)
        self.assertTrue(hasattr(signal, 'zaak'))

    def test_create_case_with_case(self):
        zaak_signal = ZaakSignalFactory()
        create_case(zaak_signal.signal)

    @override_settings(ZTC_ZAAKTYPE_URL='no_url')
    def test_create_case_with_error(self):
        signal = SignalFactory()

        with self.assertRaises(CaseNotCreatedException):
            create_case(signal)

    @expectedFailure
    def test_connect_signal_to_case(self):
        # This test will only pass once it is connected to the staging database.
        signal = SignalFactory()
        create_case(signal)
        connect_signal_to_case(signal)

    @override_settings(ZRC_ZAAKOBJECT_TYPE='random')
    def test_connect_signal_to_case_error(self):
        zaak_signal = ZaakSignalFactory()

        with self.assertRaises(ClientError):
            connect_signal_to_case(zaak_signal.signal)

    @expectedFailure
    def test_add_status_to_case(self):
        # TODO: This test needs to be fixed.
        zaak_signal = ZaakSignalFactory()
        add_status_to_case(zaak_signal.signal)

    @expectedFailure
    def test_create_document(self):
        # Waiting on staging before this can be completed.
        signal = SignalFactoryWithImage()
        create_document(signal)

    def test_create_document_with_error(self):
        signal = SignalFactory()

        with self.assertRaises(ValueError):
            create_document(signal)

    @expectedFailure
    def test_add_document_to_case(self):
        # Waiting on staging before this can be completed.
        signal = SignalFactoryWithImage()
        create_document(signal)
        add_document_to_case(signal)

    @expectedFailure
    def test_add_document_to_case_with_error(self):
        # Waiting on staging before this can be completed.
        signal = SignalFactoryWithImage()
        create_document(signal)
        add_document_to_case(signal)
