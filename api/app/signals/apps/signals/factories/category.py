import factory
from django.utils.text import slugify
from factory import fuzzy

from signals.apps.signals.models import Category


class ParentCategoryFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Parent category {}'.format(n))
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    handling = fuzzy.FuzzyChoice([c[0] for c in Category.HANDLING_CHOICES])
    handling_message = 'Test handling message (parent category)'
    is_active = True

    class Meta:
        model = Category
        django_get_or_create = ('slug', )

    @factory.post_generation
    def questions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for question in extracted:
                self.questions.add(question)


class CategoryFactory(factory.DjangoModelFactory):
    parent = factory.SubFactory('signals.apps.signals.factories.category.ParentCategoryFactory')
    name = factory.Sequence(lambda n: 'Category {}'.format(n))
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    handling = fuzzy.FuzzyChoice([c[0] for c in Category.HANDLING_CHOICES])
    handling_message = 'Test handling message (child category)'
    is_active = True

    class Meta:
        model = Category
        django_get_or_create = ('parent', 'slug', )

    @factory.post_generation
    def departments(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for department in extracted:
                self.departments.add(
                    department,
                    through_defaults={
                        'is_responsible': True,
                        'can_view': True
                    }
                )

    @factory.post_generation
    def questions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for question in extracted:
                self.questions.add(question)
