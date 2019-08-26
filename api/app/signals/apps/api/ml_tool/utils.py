from urllib.parse import urlparse

from django.urls import resolve
from rest_framework.reverse import reverse

from signals.apps.signals.models import Category


def get_category_from_prediction(category_url):
    resolved = resolve(urlparse(category_url).path)
    if not hasattr(resolved, 'kwargs'):
        return category_url, False

    slug = resolved.kwargs['sub_slug'] if 'sub_slug' in resolved.kwargs else resolved.kwargs['slug']

    category = Category.objects.get(slug=slug)
    if category.is_translated():
        return category.translated_to()
    return category


def translate_prediction_category_url(category_url, request=None):
    try:
        category = get_category_from_prediction(category_url)
    except Category.DoesNotExist:
        return category_url, False

    if category.is_child():
        translated = reverse('v1:category-detail',
                             kwargs={'slug': category.parent.slug, 'sub_slug': category.slug},
                             request=request)
    else:
        translated = reverse('v1:category-detail', kwargs={'slug': category.slug}, request=request)

    return translated, True
