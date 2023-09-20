# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import logging

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver

logger = logging.getLogger(__name__)


class CustomPermission(models.Model):
    """
    An abstract class for creating custom permissions that do not belong to any existing model.

    Django's built-in auth Permissions require a ContentType association.
    """
    class Meta:
        abstract = True


@receiver(post_migrate)
def sync_custom_permissions(sender, **kwargs):
    """
    Synchronize custom permissions after a migration.

    This function listens to the post_migrate signal in Django and creates custom permissions
    if they do not already exist.

    These custom permissions are associated with the CustomPermission model.

    Args:
        sender: The sender of the signal (usually the app with the migrations).
        **kwargs: Additional keyword arguments provided by the signal.
    """
    content_type = ContentType.objects.get_for_model(CustomPermission, for_concrete_model=False)

    custom_permissions = [
        # Custom permission to allow users to create i18next translation files.
        ('sia_add_i18next_translation_file', 'Can create i18next translation file')
    ]

    for codename, name in custom_permissions:
        if not Permission.objects.filter(name=name, codename=codename, content_type=content_type).exists():
            logger.info(f'Creating custom permission "{codename}" with name "{name}"')
            Permission.objects.create(name=name, codename=codename, content_type=content_type)
