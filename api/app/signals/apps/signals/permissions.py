from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

SIA_BACKOFFICE = 'sia_backoffice'
SIA_READ = 'sia_read'
SIA_WRITE = 'sia_write'


class CategoryPermissions:

    @staticmethod
    def create_for_all_categories():
        from signals.apps.signals.models import SubCategory

        categories = SubCategory.objects.filter(permission__isnull=True)

        for category in categories:
            CategoryPermissions.create_for_category(category)

    @staticmethod
    def create_for_category(category):
        from signals.apps.signals.models import Signal

        with transaction.atomic():
            permission = Permission(
                codename='category_access_' + str(category.id),
                content_type=ContentType.objects.get_for_model(Signal),
                name='Category access - ' + category.name
            )
            permission.save()
            category.permission = permission
            category.save()
