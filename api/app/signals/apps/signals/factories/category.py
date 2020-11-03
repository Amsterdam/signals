from django.utils.text import slugify
from factory import DjangoModelFactory, LazyAttribute, Sequence, SubFactory, post_generation
from factory.fuzzy import FuzzyChoice

from signals.apps.signals.models import Category


class ParentCategoryFactory(DjangoModelFactory):
    name = Sequence(lambda n: 'Parent category {}'.format(n))
    slug = LazyAttribute(lambda o: slugify(o.name))
    handling = FuzzyChoice([c[0] for c in Category.HANDLING_CHOICES])
    handling_message = 'Test handling message (parent category)'
    is_active = True

    class Meta:
        model = Category
        django_get_or_create = ('slug', )

    @post_generation
    def questions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for question in extracted:
                self.questions.add(question)


class CategoryFactory(DjangoModelFactory):
    parent = SubFactory('signals.apps.signals.factories.category.ParentCategoryFactory')
    name = Sequence(lambda n: 'Category {}'.format(n))
    slug = LazyAttribute(lambda o: slugify(o.name))
    handling = FuzzyChoice([c[0] for c in Category.HANDLING_CHOICES])
    handling_message = 'Test handling message (child category)'
    is_active = True

    class Meta:
        model = Category
        django_get_or_create = ('parent', 'slug', )

    @post_generation
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

    @post_generation
    def questions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for question in extracted:
                self.questions.add(question)
