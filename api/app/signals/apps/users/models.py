from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext as _

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class Profile(CreatedUpdatedModel):
    """
    The profile model for a user
    """

    user = models.OneToOneField(
        to=User,
        related_name='profile',
        verbose_name=_('profile'),
        on_delete=models.DO_NOTHING,
    )

    def __str__(self):
        return self.user.username
