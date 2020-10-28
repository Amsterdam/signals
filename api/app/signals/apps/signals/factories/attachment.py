import factory

from signals.apps.signals.models import Attachment


class ImageAttachmentFactory(factory.DjangoModelFactory):

    class Meta:
        model = Attachment

    _signal = factory.SubFactory('signals.apps.signals.factories.signal.SignalFactory')
    created_by = factory.Sequence(lambda n: 'veelmelder{}@example.com'.format(n))
    file = factory.django.ImageField()  # In reality it's a FileField, but we want to force an image
    is_image = True

    @factory.post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
        self.is_image = True
        self.save()
