from urllib.parse import urlparse

from django.urls import resolve
from rest_framework.reverse import reverse

from signals.apps.signals.models import Category


def get_category_from_prediction(category_url):
    """
    Extract category from category URL.
    """
    resolved = resolve(urlparse(category_url).path)
    if not hasattr(resolved, 'kwargs'):
        return category_url, False

    slug = resolved.kwargs['slug']
    parent_slug = resolved.kwargs.get('parent_lookup_parent__slug', None)

    if not parent_slug:
        category = Category.objects.get(slug=slug, parent__isnull=True)
    else:
        category = Category.objects.get(slug=slug, parent__slug=parent_slug)

    return category


def get_clean_category_url(category_url, request=None):
    """
    Check that category referred to exists and clean up the category URL.
    """
    # Note: predictions from the ML tool service have no host set.
    try:
        category = get_category_from_prediction(category_url)
    except Category.DoesNotExist:
        return category_url, False

    return get_url_from_category(category, request=request), True


def get_url_from_category(category, request=None):
    """
    Get the public category URL for a given main or sub category.
    """
    # Note: using reverse here will set the correct host.
    if category.is_child():
        kwargs = {'parent_lookup_parent__slug': category.parent.slug, 'slug': category.slug}
        return reverse('v1:public-subcategory-detail', kwargs=kwargs, request=request)
    else:
        kwargs = {'slug': category.slug}
        return reverse('v1:public-maincategory-detail', kwargs=kwargs, request=request)
