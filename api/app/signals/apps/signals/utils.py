from django.urls import resolve


def resolve_categories(path):
    from signals.apps.signals.v1.views import MainCategoryViewSet, SubCategoryViewSet

    view, args, kwargs = resolve(path)
    if id(view.cls) == id(SubCategoryViewSet):
        sub_category = view.cls.queryset.get(slug=kwargs['sub_slug'],
                                             main_category__slug=kwargs['slug'])
        return sub_category.main_category, sub_category
    elif id(view.cls) == id(MainCategoryViewSet):
        return view.cls.queryset.get(slug=kwargs['slug']), None
