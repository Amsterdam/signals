# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from factory import Sequence, SubFactory, post_generation
from factory.django import DjangoModelFactory, FileField, ImageField

from signals.apps.signals.models import Attachment


class AttachmentFactory(DjangoModelFactory):
    class Meta:
        model = Attachment

    _signal = SubFactory('signals.apps.signals.factories.signal.SignalFactory')
    created_by = Sequence(lambda n: 'veelmelder{}@example.com'.format(n))
    file = FileField()

    @post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
        self.is_image = True
        self.save()


class ImageAttachmentFactory(AttachmentFactory):
    file = ImageField()  # In reality it's a FileField, but we want to force an image
    is_image = True
