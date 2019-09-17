import uuid

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from swift.storage import SwiftStorage

from signals.apps.signals import workflow
from signals.apps.signals.managers import SignalManager
from signals.apps.signals.models.mixins import CreatedUpdatedModel


class Signal(CreatedUpdatedModel):
    SOURCE_DEFAULT_ANONYMOUS_USER = 'online'

    # we need an unique id for external systems.
    # TODO SIG-563 rename `signal_id` to `signal_uuid` to be more specific.
    signal_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    source = models.CharField(max_length=128, default=SOURCE_DEFAULT_ANONYMOUS_USER)

    text = models.CharField(max_length=3000)
    text_extra = models.CharField(max_length=10000, default='', blank=True)

    location = models.OneToOneField('signals.Location',
                                    related_name='signal',
                                    null=True,
                                    on_delete=models.SET_NULL)
    status = models.OneToOneField('signals.Status',
                                  related_name='signal',
                                  null=True,
                                  on_delete=models.SET_NULL)
    category_assignment = models.OneToOneField('signals.CategoryAssignment',
                                               related_name='signal',
                                               null=True,
                                               on_delete=models.SET_NULL)
    categories = models.ManyToManyField('signals.Category',
                                        through='signals.CategoryAssignment')
    reporter = models.OneToOneField('signals.Reporter',
                                    related_name='signal',
                                    null=True,
                                    on_delete=models.SET_NULL)
    priority = models.OneToOneField('signals.Priority',
                                    related_name='signal',
                                    null=True,
                                    on_delete=models.SET_NULL)

    # Date of the incident.
    incident_date_start = models.DateTimeField(null=False)
    incident_date_end = models.DateTimeField(null=True)

    # Date action is expected
    operational_date = models.DateTimeField(null=True)

    # Date we should have reported back to reporter.
    expire_date = models.DateTimeField(null=True)

    # file will be saved to MEDIA_ROOT/uploads/2015/01/30
    upload = ArrayField(models.FileField(upload_to='uploads/%Y/%m/%d/'), null=True)  # TODO: remove

    extra_properties = JSONField(null=True)

    # SIG-884
    parent = models.ForeignKey(to='self', related_name='children', null=True, blank=True,
                               on_delete=models.SET_NULL)

    objects = models.Manager()
    actions = SignalManager()

    @property
    def image(self):
        """ Field for backwards compatibility. The attachment table replaces the old 'image'
        property """
        attachment = self.attachments.filter(is_image=True).first()
        return attachment.file if attachment else ""

    @property
    def image_crop(self):
        attachment = self.attachments.filter(is_image=True).first()
        return attachment.image_crop if self.image else ''

    class Meta:
        permissions = (
            ('sia_read', 'Can read from SIA'),
            ('sia_write', 'Can write to SIA'),
        )
        ordering = ('created_at',)
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['id', 'parent']),
        ]

    def __init__(self, *args, **kwargs):
        super(Signal, self).__init__(*args, **kwargs)
        if not self.signal_id:
            self.signal_id = uuid.uuid4()

    def __str__(self):
        """Identifying string.
        DO NOT expose sensitive stuff here.
        """
        state = ''
        buurt_code = ''

        if self.status:
            state = self.status.state
        if self.location:
            buurt_code = self.location.buurt_code

        return '{} - {} - {} - {}'.format(
            self.id,
            state,
            buurt_code,
            self.created_at
        )

    @property
    def sia_id(self):
        """SIA identifier used for external communication.

        :returns: str
        """
        return 'SIA-{id}'.format(id=self.id)

    def get_fqdn_image_crop_url(self):
        """Get FQDN image crop url.

        :returns: url (str) or None
        """
        if not self.image_crop:
            return None

        is_swift = isinstance(self.image_crop.storage, SwiftStorage)
        if is_swift:
            return self.image_crop.url  # Generated temp url from Swift Object Store.
        else:
            # Generating a fully qualified url ourself.
            current_site = Site.objects.get_current()
            is_local = 'localhost' in current_site.domain or settings.DEBUG
            fqdn_url = '{scheme}://{domain}{path}'.format(
                scheme='http' if is_local else 'https',
                domain=current_site.domain,
                path=self.image_crop.url)
            return fqdn_url

    def is_parent(self):
        # If we have children we are a parent
        return self.children.exists()

    def is_child(self):
        # If we have a parent we are a child
        return self.parent is not None

    @property
    def siblings(self):
        if self.is_child():
            # If we are a child return all siblings
            siblings_qs = self.parent.children.all()
            if self.pk:
                # Exclude myself if possible
                return siblings_qs.exclude(pk=self.pk)
            return siblings_qs

        # Return a non queryset
        return self.__class__.objects.none()

    def _validate(self):
        if self.is_parent() and self.is_child():
            # We cannot be a parent and a child at once
            raise ValidationError('Cannot be a parent and a child at the once')

        if self.parent and self.parent.is_child():
            # The parent of this Signal cannot be a child of another Signal
            raise ValidationError('A child of a child is not allowed')

        if (self.pk is None and self.is_child() and
                self.siblings.count() >= settings.SIGNAL_MAX_NUMBER_OF_CHILDREN):
            # we are a new child and our parent already has the max number of children
            raise ValidationError('Maximum number of children reached for the parent Signal')

        if self.children.exists() and self.status.state != workflow.GESPLITST:
            # If we have children our status can only be "gesplitst"
            raise ValidationError('The status of a parent Signal can only be "gesplitst"')

    def save(self, *args, **kwargs):
        self._validate()
        super(Signal, self).save(*args, **kwargs)
