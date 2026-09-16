# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from django.db.models import Q
from django_filters.rest_framework import FilterSet, filters

from signals.apps.signals.models import Category


class QuestionFilterSet(FilterSet):
    main_slug = filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True, parent__isnull=True).all(),
        to_field_name='slug',
        field_name='category__slug',
        label='Hoofd categorie',
    )
    sub_slug = filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True, parent__isnull=False).all(),
        to_field_name='slug',
        field_name='category__parent__slug',
        label='Sub categorie',
    )

    def filter_queryset(self, queryset):
        main_cat = self.form.cleaned_data.get('main_slug', None)
        main_slug = main_cat.slug if main_cat else None
        sub_cat = self.form.cleaned_data.get('sub_slug', None)
        sub_slug = sub_cat.slug if sub_cat else None

        if not main_slug:
            # Without a category there is no such thing as "the" position of a
            # question: a question that is linked to several categories has one
            # position per category. Ordering on those multi-valued columns puts
            # them in the SELECT, which breaks the DISTINCT on the queryset and
            # returns a question once per category it is linked to. Order on the
            # question itself instead, so every question is returned exactly once.
            # The key is not unique, so pk is used to keep paging deterministic.
            return queryset.filter(category__is_active=True).distinct().order_by('key', 'pk')

        # sort on main category first, then question ordering
        qs = queryset.filter(category__is_active=True).order_by(
            '-categoryquestion__category__parent', 'categoryquestion__order'
        )

        if sub_slug:
            childq = Q(category__parent__slug=main_slug) & Q(category__slug=sub_slug)
            parentq = Q(category__parent__isnull=True) & Q(category__slug=main_slug)
            qs = qs.filter(childq | parentq)
        else:
            qs = qs.filter(
                category__parent__isnull=True,
                category__slug=main_slug
            )
        return qs
