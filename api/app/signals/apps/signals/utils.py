from django.urls import resolve

from signals.apps.signals.views import MainCategoryViewSet, SubCategoryViewSet


def resolve_categories(path):
    view, args, kwargs = resolve(path)
    if view.cls is SubCategoryViewSet:
        sub_category = view.cls.queryset.get(slug=kwargs['sub_slug'],
                                             main_category__slug=kwargs['slug'])
        return sub_category.main_category, sub_category
    elif view.cls is MainCategoryViewSet:
        return view.cls.queryset.get(slug=kwargs['slug']), None
