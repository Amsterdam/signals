from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

from signals.apps.signals.models.mixins import CreatedUpdatedModel

User = get_user_model()


class Profile(CreatedUpdatedModel):
    """
    The profile model for a user
    """

    user = models.OneToOneField(
        to=User,
        related_name='profile',
        verbose_name=_('profile'),
        on_delete=models.CASCADE,
    )

    departments = models.ManyToManyField(
        to='signals.Department'
    )

    # SIG-2016 Added a note field to the profile
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)


class SignalUser(CreatedUpdatedModel):
    """
    relation for assigning user to signal
    """

    _signal = models.OneToOneField('signals.Signal', related_name='user_assignment', on_delete=models.CASCADE, blank=True) # noqa
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True)
    created_by = models.EmailField(null=True, blank=True)
