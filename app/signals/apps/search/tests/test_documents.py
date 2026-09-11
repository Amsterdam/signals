# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
from django.test import TestCase

from signals.apps.search.documents.signal import SignalDocument
from signals.apps.signals.factories import SignalFactory


class TestSignalDocumentPrepareBatch(TestCase):
    """
    prepare_batch() drives the Elasticsearch indexing path over the queryset from
    get_queryset(), which uses prefetch_related(). Django requires an explicit
    chunk_size for QuerySet.iterator() on such a queryset; omitting it raises
    ValueError as of Django 5.0.

    This path has no other test coverage (signals/apps/search/* is excluded from
    the coverage report), so it is asserted explicitly here.
    """

    def test_prepare_batch_yields_a_document_per_signal(self) -> None:
        signals = SignalFactory.create_batch(3)

        documents = list(SignalDocument.prepare_batch(SignalDocument().get_queryset()))

        self.assertEqual(len(documents), 3)
        self.assertEqual(
            {document['_id'] for document in documents},
            {signal.id for signal in signals},
        )
