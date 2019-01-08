from uuid import uuid4

import factory
from django.conf import settings

from tests.apps.signals.factories import SignalFactory


class CaseSignalFactory(factory.DjangoModelFactory):

    class Meta:
        model = "zds.CaseSignal"

    signal = factory.SubFactory(SignalFactory)
    zrc_link = factory.lazy_attribute(lambda obj: '{}/zrc/api/v1/zaken/{}'.format(
        settings.ZRC_URL, uuid4()))


class CaseStatusFactory(factory.DjangoModelFactory):

    class Meta:
        model = "zds.CaseStatus"

    case_signal = factory.SubFactory(CaseSignalFactory)
    zrc_link = 'http://amsterdam.nl/'


class CaseDocumentFactory(factory.DjangoModelFactory):

    class Meta:
        model = "zds.CaseDocument"

    case_signal = factory.SubFactory(CaseSignalFactory)
    drc_link = 'http://amsterdam.nl/'
