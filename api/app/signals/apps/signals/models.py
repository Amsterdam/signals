import copy
import imghdr
import logging
import uuid

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.postgres.fields import ArrayField, JSONField
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from imagekit import ImageSpec
from imagekit.cachefiles import ImageCacheFile
from imagekit.processors import ResizeToFit
from swift.storage import SwiftStorage

from signals.apps.signals import workflow
from signals.apps.signals.managers import SignalManager
from signals.apps.signals.workflow import STATUS_CHOICES

logger = logging.getLogger(__name__)


class CreatedUpdatedModel(models.Model):
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        abstract = True


class Buurt(models.Model):
    ogc_fid = models.IntegerField(primary_key=True)
    id = models.CharField(max_length=14)
    vollcode = models.CharField(max_length=4)
    naam = models.CharField(max_length=40)

    class Meta:
        db_table = 'buurt_simple'


class Signal(CreatedUpdatedModel):
    # we need an unique id for external systems.
    # TODO SIG-563 rename `signal_id` to `signal_uuid` to be more specific.
    signal_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    source = models.CharField(max_length=128, default='public-api')

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
    upload = ArrayField(models.FileField(upload_to='uploads/%Y/%m/%d/'), null=True)

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

        if (self.is_child() and
                self.siblings.count() >= settings.SIGNAL_MAX_NUMBER_OF_CHILDREN):
            # we are a child and our parent already has the max number of children
            raise ValidationError('Maximum number of children reached for the parent Signal')

        if self.children.exists() and self.status.state != workflow.GESPLITST:
            # If we have children our status can only be "gesplitst"
            raise ValidationError('The status of a parent Signal can only be "gesplitst"')

    def save(self, *args, **kwargs):
        self._validate()
        super(Signal, self).save(*args, **kwargs)


STADSDEEL_CENTRUM = 'A'
STADSDEEL_WESTPOORT = 'B'
STADSDEEL_WEST = 'E'
STADSDEEL_OOST = 'M'
STADSDEEL_NOORD = 'N'
STADSDEEL_ZUIDOOST = 'T'
STADSDEEL_ZUID = 'K'
STADSDEEL_NIEUWWEST = 'F'
STADSDELEN = (
    (STADSDEEL_CENTRUM, 'Centrum'),
    (STADSDEEL_WESTPOORT, 'Westpoort'),
    (STADSDEEL_WEST, 'West'),
    (STADSDEEL_OOST, 'Oost'),
    (STADSDEEL_NOORD, 'Noord'),
    (STADSDEEL_ZUIDOOST, 'Zuidoost'),
    (STADSDEEL_ZUID, 'Zuid'),
    (STADSDEEL_NIEUWWEST, 'Nieuw-West'),
)


def get_buurt_code_choices():
    return Buurt.objects.values_list('vollcode', 'naam')


def get_address_text(location, short=False):
    """Generate address text, shortened if needed."""

    field_prefixes = (
        ('openbare_ruimte', ''),
        ('huisnummer', ' '),
        ('huisletter', ''),
        ('huisnummer_toevoeging', '-'),
        ('postcode', ' '),
        ('woonplaats', ' ')
    )

    if short:
        field_prefixes = field_prefixes[:-2]

    address_text = ''
    if location.address and isinstance(location.address, dict):
        for field, prefix in field_prefixes:
            if field in location.address and location.address[field]:
                address_text += prefix + str(location.address[field])

    return address_text


class Location(CreatedUpdatedModel):
    """All location related information."""

    _signal = models.ForeignKey(
        "signals.Signal", related_name="locations",
        null=False, on_delete=models.CASCADE
    )

    geometrie = models.PointField(name="geometrie")
    stadsdeel = models.CharField(
        null=True, max_length=1, choices=STADSDELEN)
    # we do NOT use foreign key, since we update
    # buurten as external data in a seperate process
    buurt_code = models.CharField(null=True, max_length=4)
    address = JSONField(null=True)
    address_text = models.CharField(null=True, max_length=256, editable=False)
    created_by = models.EmailField(null=True, blank=True)

    extra_properties = JSONField(null=True)
    bag_validated = models.BooleanField(default=False)

    @property
    def short_address_text(self):
        return get_address_text(self, short=True)

    def set_address_text(self):
        self.address_text = get_address_text(self)

    def save(self, *args, **kwargs):
        # Set address_text
        self.set_address_text()
        super().save(*args, **kwargs)  # Call the "real" save() method.

    def get_rd_coordinates(self):
        to_transform = copy.deepcopy(self.geometrie)
        to_transform.transform(
            CoordTransform(
                SpatialReference(4326),  # WGS84
                SpatialReference(28992)  # RD
            )
        )
        return to_transform


class Reporter(CreatedUpdatedModel):
    """Privacy sensitive information on reporter."""

    _signal = models.ForeignKey(
        "signals.Signal", related_name="reporters",
        null=False, on_delete=models.CASCADE
    )

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=17, blank=True)
    remove_at = models.DateTimeField(null=True)

    extra_properties = JSONField(null=True)  # TODO: candidate for removal


class CategoryAssignment(CreatedUpdatedModel):
    """Many-to-Many through model for `Signal` <-> `Category`."""
    _signal = models.ForeignKey('signals.Signal',
                                on_delete=models.CASCADE,
                                related_name='category_assignments')
    category = models.ForeignKey('signals.Category',
                                 on_delete=models.CASCADE,
                                 related_name='category_assignments')
    created_by = models.EmailField(null=True, blank=True)

    extra_properties = JSONField(null=True)  # TODO: candidate for removal

    def __str__(self):
        """String representation."""
        return '{sub} - {signal}'.format(sub=self.category, signal=self._signal)


class Status(CreatedUpdatedModel):
    TARGET_API_SIGMAX = 'sigmax'
    TARGET_API_CHOICES = (
        (TARGET_API_SIGMAX, 'Sigmax (City Control)'),
    )

    _signal = models.ForeignKey('signals.Signal', related_name='statuses', on_delete=models.CASCADE)

    text = models.CharField(max_length=10000, null=True, blank=True)
    # TODO, rename field to `email` it's not a `User` it's a `email`...
    user = models.EmailField(null=True, blank=True)
    target_api = models.CharField(max_length=250, null=True, blank=True, choices=TARGET_API_CHOICES)
    state = models.CharField(max_length=20,
                             blank=True,
                             choices=workflow.STATUS_CHOICES,
                             default=workflow.GEMELD,
                             help_text='Melding status')

    # TODO, do we need this field or can we remove it?
    extern = models.BooleanField(default=False, help_text='Wel of niet status extern weergeven')

    extra_properties = JSONField(null=True, blank=True)

    class Meta:
        permissions = (
            ('push_to_sigmax', 'Push to Sigmax/CityControl'),
        )
        verbose_name_plural = 'Statuses'
        get_latest_by = 'datetime'
        ordering = ('created_at',)

    def __str__(self):
        return str(self.text)

    # TODO: Maybe migrate user to created_by, for now made this work-around
    @property
    def created_by(self):
        return self.user

    @created_by.setter
    def created_by(self, created_by):
        self.user = created_by

    def clean(self):
        """Validate instance.

        Most important validation is the state transition.

        :raises: ValidationError
        :returns:
        """
        errors = {}

        if self._signal.status:
            # We already have a status so let's check if the new status can be set
            current_state = self._signal.status.state
            current_state_display = self._signal.status.get_state_display()
        else:
            # No status has been set yet so we default to LEEG
            current_state = workflow.LEEG
            current_state_display = workflow.LEEG

            logger.warning('Signal #{} has status set to None'.format(self._signal.pk))

        new_state = self.state
        new_state_display = self.get_state_display()

        # Validating state transition.
        if new_state not in workflow.ALLOWED_STATUS_CHANGES[current_state]:
            error_msg = 'Invalid state transition from `{from_state}` to `{to_state}`.'.format(
                from_state=current_state_display,
                to_state=new_state_display)
            errors['state'] = ValidationError(error_msg, code='invalid')

        # Validating state "TE_VERZENDEN".
        if new_state == workflow.TE_VERZENDEN and not self.target_api:
            error_msg = 'This field is required when changing `state` to `{new_state}`.'.format(
                new_state=new_state_display)
            errors['target_api'] = ValidationError(error_msg, code='required')

        if new_state != workflow.TE_VERZENDEN and self.target_api:
            error_msg = 'This field can only be set when changing `state` to `{state}`.'.format(
                state=workflow.TE_VERZENDEN)
            errors['target_api'] = ValidationError(error_msg, code='invalid')

        # Validating text field required.
        if new_state in [workflow.AFGEHANDELD, workflow.HEROPEND] and not self.text:
            error_msg = 'This field is required when changing `state` to `{new_state}`.'.format(
                new_state=new_state_display)
            errors['text'] = ValidationError(error_msg, code='required')

        if errors:
            raise ValidationError(errors)


class Priority(CreatedUpdatedModel):
    PRIORITY_NORMAL = 'normal'
    PRIORITY_HIGH = 'high'
    PRIORITY_CHOICES = (
        (PRIORITY_NORMAL, 'Normal'),
        (PRIORITY_HIGH, 'High'),
    )

    _signal = models.ForeignKey('signals.Signal',
                                related_name='priorities',
                                null=False,
                                on_delete=models.CASCADE)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)
    created_by = models.EmailField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Priorities'

    def __str__(self):
        """String representation."""
        return self.get_priority_display()


#
# Category terms
#


class MainCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Main Categories'

    def __str__(self):
        """String representation."""
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Category(models.Model):
    HANDLING_A3DMC = 'A3DMC'
    HANDLING_A3DEC = 'A3DEC'
    HANDLING_A3WMC = 'A3WMC'
    HANDLING_A3WEC = 'A3WEC'
    HANDLING_I5DMC = 'I5DMC'
    HANDLING_STOPEC = 'STOPEC'
    HANDLING_KLOKLICHTZC = 'KLOKLICHTZC'
    HANDLING_GLADZC = 'GLADZC'
    HANDLING_A3DEVOMC = 'A3DEVOMC'
    HANDLING_WS1EC = 'WS1EC'
    HANDLING_WS2EC = 'WS2EC'
    HANDLING_REST = 'REST'
    HANDLING_CHOICES = (
        (HANDLING_A3DMC, HANDLING_A3DMC),
        (HANDLING_A3DEC, HANDLING_A3DEC),
        (HANDLING_A3WMC, HANDLING_A3WMC),
        (HANDLING_A3WEC, HANDLING_A3WEC),
        (HANDLING_I5DMC, HANDLING_I5DMC),
        (HANDLING_STOPEC, HANDLING_STOPEC),
        (HANDLING_KLOKLICHTZC, HANDLING_KLOKLICHTZC),
        (HANDLING_GLADZC, HANDLING_GLADZC),
        (HANDLING_A3DEVOMC, HANDLING_A3DEVOMC),
        (HANDLING_WS1EC, HANDLING_WS1EC),
        (HANDLING_WS2EC, HANDLING_WS2EC),
        (HANDLING_REST, HANDLING_REST),
    )

    main_category = models.ForeignKey('signals.MainCategory',
                                      related_name='categories',
                                      on_delete=models.PROTECT)
    slug = models.SlugField()
    name = models.CharField(max_length=255)
    handling = models.CharField(max_length=20, choices=HANDLING_CHOICES)
    departments = models.ManyToManyField('signals.Department')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('name',)
        unique_together = ('main_category', 'slug',)
        verbose_name_plural = 'Sub Categories'

    def __str__(self):
        """String representation."""
        return '{name} ({main_category})'.format(name=self.name,
                                                 main_category=self.main_category.name)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Department(models.Model):
    code = models.CharField(max_length=3)
    name = models.CharField(max_length=255)
    is_intern = models.BooleanField(default=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        """String representation."""
        return '{code} ({name})'.format(code=self.code, name=self.name)


class Note(CreatedUpdatedModel):
    """Notes field for `Signal` instance."""
    _signal = models.ForeignKey('signals.Signal',
                                related_name='notes',
                                null=False,
                                on_delete=models.CASCADE)
    text = models.TextField(max_length=3000)
    created_by = models.EmailField(null=True, blank=True)  # analoog Priority model

    class Meta:
        ordering = ('-created_at',)


class History(models.Model):
    identifier = models.CharField(primary_key=True, max_length=255)
    _signal = models.ForeignKey('signals.Signal',
                                related_name='history',
                                null=False,
                                on_delete=models.CASCADE)
    when = models.DateTimeField(null=True)
    what = models.CharField(max_length=255)
    who = models.CharField(max_length=255, null=True)  # old entries in database may have no user
    extra = models.CharField(max_length=255, null=True)  # not relevant for every logged model.
    description = models.TextField(max_length=3000)

    # No changes to this database view please!
    def save(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError

    @property
    def action(self):
        """Generate text for the action field that can serve as title in UI."""
        if self.what == 'UPDATE_STATUS':
            return 'Update status naar: {}'.format(
                dict(STATUS_CHOICES).get(self.extra, 'Onbekend'))
        elif self.what == 'UPDATE_PRIORITY':
            return 'Prioriteit update naar: {}'.format(
                dict(Priority.PRIORITY_CHOICES).get(self.extra, 'Onbekend'))
        elif self.what == 'UPDATE_CATEGORY_ASSIGNMENT':
            return 'Categorie gewijzigd naar: {}'.format(self.extra)
        elif self.what == 'CREATE_NOTE' or self.what == 'UPDATE_LOCATION':
            return self.extra
        return 'Actie onbekend.'

    class Meta:
        managed = False
        db_table = 'signals_history_view'


class Attachment(CreatedUpdatedModel):
    created_by = models.EmailField(null=True, blank=True)
    _signal = models.ForeignKey(
        "signals.Signal",
        null=False,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    file = models.FileField(
        upload_to='attachments/%Y/%m/%d/',
        null=False,
        blank=False,
        max_length=255
    )
    mimetype = models.CharField(max_length=30, blank=False, null=False)
    is_image = models.BooleanField(default=False)

    class Meta:
        ordering = ('created_at',)

    class NotAnImageException(Exception):
        pass

    class CroppedImage(ImageSpec):
        processors = [ResizeToFit(800, 800), ]
        format = 'JPEG'
        options = {'quality': 80}

    @property
    def image_crop(self):
        return self._crop_image()

    def _crop_image(self):
        if not self.is_image:
            raise Attachment.NotAnImageException("Attachment is not an image. Use is_image to check"
                                                 " if attachment is an image before asking for the "
                                                 "cropped version.")

        generator = Attachment.CroppedImage(source=self.file)
        cache_file = ImageCacheFile(generator)

        try:
            cache_file.generate()
        except FileNotFoundError as e:
            logger.warn("File not found when generating cache file: " + str(e))

        return cache_file

    def save(self, *args, **kwargs):
        if self.pk is None:
            # Check if file is image
            self.is_image = imghdr.what(self.file) is not None

            if not self.mimetype and hasattr(self.file.file, 'content_type'):
                self.mimetype = self.file.file.content_type

        super().save(*args, **kwargs)
