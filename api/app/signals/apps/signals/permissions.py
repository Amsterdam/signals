from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

SIA_ALL_CATEGORIES = 'sia_all_categories'
SIA_READ = 'sia_read'
SIA_WRITE = 'sia_write'


class CategoryPermissions:

    @staticmethod
    def create_for_all_categories():
        from signals.apps.signals.models import Category

        categories = Category.objects.filter(permission__isnull=True)

        for category in categories:
            CategoryPermissions.create_for_category(category)

    @staticmethod
    def create_for_category(category):
        from signals.apps.signals.models import Signal

        with transaction.atomic():
            permission = Permission(
                codename='category_access_' + str(category.id),
                content_type=ContentType.objects.get_for_model(Signal),
            )
            permission.save()
            category.permission = permission
            category.save()
