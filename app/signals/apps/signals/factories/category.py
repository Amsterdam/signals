# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from django.utils.text import slugify
from factory import LazyAttribute, Sequence, SubFactory, post_generation
from factory.django import DjangoModelFactory, ImageField
from factory.fuzzy import FuzzyChoice

from signals.apps.signals.models import Category


class ParentCategoryFactory(DjangoModelFactory):
    name = Sequence(lambda n: 'Parent category {}'.format(n))
    slug: LazyAttribute = LazyAttribute(lambda o: slugify(o.name))
    handling :FuzzyChoice = FuzzyChoice([c[0] for c in Category.HANDLING_CHOICES])
    handling_message = 'Test handling message (parent category)'
    is_active = True
    questionnaire = None
    public_name = None
    is_public_accessible = False

    class Meta:
        model = Category
        django_get_or_create = ('slug',)
        skip_postgeneration_save = True

    @post_generation
    def questions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for question in extracted:
                self.questions.add(question)
            self.save()


class CategoryFactory(DjangoModelFactory):
    parent: SubFactory = SubFactory('signals.apps.signals.factories.category.ParentCategoryFactory')
    name = Sequence(lambda n: 'Category {}'.format(n))
    slug: LazyAttribute = LazyAttribute(lambda o: slugify(o.name))
    handling :FuzzyChoice = FuzzyChoice([c[0] for c in Category.HANDLING_CHOICES])
    handling_message = 'Test handling message (child category)'
    is_active = True
    questionnaire = None
    public_name = None
    is_public_accessible = False

    class Meta:
        model = Category
        django_get_or_create = ('parent', 'slug',)
        skip_postgeneration_save = True

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
            self.save()

    @post_generation
    def questions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for question in extracted:
                self.questions.add(question)
            self.save()


class CategoryWithIconFactory(CategoryFactory):
    icon = ImageField()
