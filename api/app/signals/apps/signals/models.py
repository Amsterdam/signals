import uuid

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import transaction
from django.dispatch import Signal as DjangoSignal

# Declaring custom Django signals for our `SignalManager`.
create_initial = DjangoSignal(providing_args=['signal_obj'])
update_location = DjangoSignal(providing_args=['signal_obj', 'location', 'prev_location'])
update_status = DjangoSignal(providing_args=['signal_obj', 'status', 'prev_status'])
update_category = DjangoSignal(providing_args=['signal_obj', 'category', 'prev_category'])
update_reporter = DjangoSignal(providing_args=['signal_obj', 'reporter', 'prev_reporter'])
update_priority = DjangoSignal(providing_args=['signal_obj', 'priority', 'prev_priority'])


class SignalManager(models.Manager):

    def create_initial(self,
                       signal_data,
                       location_data,
                       status_data,
                       category_data,
                       reporter_data,
                       priority_data=None):
        """Create a new `Signal` object with all related objects.

        :param signal_data: deserialized data dict
        :param location_data: deserialized data dict
        :param status_data: deserialized data dict
        :param category_data: deserialized data dict
        :param reporter_data: deserialized data dict
        :param priority_data: deserialized data dict (Default: None)
        :returns: Signal object
        """
        with transaction.atomic():
            signal = self.create(**signal_data)

            # Set default (empty dict) value for `priority_data` if None is given.
            priority_data = priority_data or {}

            # Create dependent model instances with correct foreign keys to Signal
            location = Location.objects.create(**location_data, _signal_id=signal.pk)
            status = Status.objects.create(**status_data, _signal_id=signal.pk)
            category = Category.objects.create(**category_data, _signal_id=signal.pk)
            reporter = Reporter.objects.create(**reporter_data, _signal_id=signal.pk)
            priority = Priority.objects.create(**priority_data, _signal_id=signal.pk)

            # Set Signal to dependent model instance foreign keys
            signal.location = location
            signal.status = status
            signal.category = category
            signal.reporter = reporter
            signal.priority = priority
            signal.save()

            transaction.on_commit(lambda: create_initial.send(sender=self.__class__,
                                                              signal_obj=signal))

        return signal

    def update_location(self, data, signal):
        """Update (create new) `Location` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Location object
        """
        with transaction.atomic():
            prev_location = signal.location

            location = Location.objects.create(**data, _signal_id=signal.id)
            signal.location = location
            signal.save()

            transaction.on_commit(lambda: update_location.send(sender=self.__class__,
                                                               signal_obj=signal,
                                                               location=location,
                                                               prev_location=prev_location))

        return location

    def update_status(self, data, signal):
        """Update (create new) `Status` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Status object
        """
        with transaction.atomic():
            prev_status = signal.status

            status = Status.objects.create(**data, _signal_id=signal.id)
            signal.status = status
            signal.save()

            transaction.on_commit(lambda: update_status.send(sender=self.__class__,
                                                             signal_obj=signal,
                                                             status=status,
                                                             prev_status=prev_status))

        return status

    def update_category(self, data, signal):
        """Update (create new) `Category` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Category object
        """
        with transaction.atomic():
            prev_category = signal.category

            category = Category.objects.create(**data, _signal_id=signal.id)
            signal.category = category
            signal.save()

            transaction.on_commit(lambda: update_category.send(sender=self.__class__,
                                                               signal_obj=signal,
                                                               category=category,
                                                               prev_category=prev_category))

        return category

    def update_reporter(self, data, signal):
        """Update (create new) `Reporter` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Reporter object
        """
        with transaction.atomic():
            prev_reporter = signal.reporter

            reporter = Reporter.objects.create(**data, _signal_id=signal.id)
            signal.reporter = reporter
            signal.save()

            transaction.on_commit(lambda: update_reporter.send(sender=self.__class__,
                                                               signal_obj=signal,
                                                               reporter=reporter,
                                                               prev_reporter=prev_reporter))

        return reporter

    def update_priority(self, data, signal):
        """Update (create new) `Priority` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Priority object
        """
        with transaction.atomic():
            prev_priority = signal.priority

            priority = Priority.objects.create(**data, _signal_id=signal.id)
            signal.priority = priority
            signal.save()

            transaction.on_commit(lambda: update_priority.send(sender=self.__class__,
                                                               signal_obj=signal,
                                                               priority=priority,
                                                               prev_priority=prev_priority))

        return priority


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

    text = models.CharField(max_length=1000)
    text_extra = models.CharField(max_length=10000, default='', blank=True)

    location = models.OneToOneField('signals.Location',
                                    related_name='signal',
                                    null=True,
                                    on_delete=models.SET_NULL)
    status = models.OneToOneField('signals.Status',
                                  related_name='signal',
                                  null=True,
                                  on_delete=models.SET_NULL)
    category = models.OneToOneField('signals.Category',
                                    related_name='signal',
                                    null=True,
                                    on_delete=models.SET_NULL)
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
    image = models.ImageField(upload_to='images/%Y/%m/%d/', null=True, blank=True)

    # file will be saved to MEDIA_ROOT/uploads/2015/01/30
    upload = ArrayField(models.FileField(upload_to='uploads/%Y/%m/%d/'), null=True)

    extra_properties = JSONField(null=True)

    objects = models.Manager()
    actions = SignalManager()

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

    extra_properties = JSONField(null=True)

    def set_address_text(self):
        field_prefixes = (
            ('openbare_ruimte', ''),
            ('huisnummer', ' '),
            ('huisletter', ''),
            ('huisnummer_toevoeging', '-'),
            ('postcode', ' '),
            ('woonplaats', ' ')
        )
        address_text = ''
        if self.address and isinstance(self.address, dict):
            for field, prefix in field_prefixes:
                if field in self.address and self.address[field]:
                    address_text += prefix + str(self.address[field])
            self.address_text = address_text

    def save(self, *args, **kwargs):
        # Set address_text
        self.set_address_text()
        super().save(*args, **kwargs)  # Call the "real" save() method.


class Reporter(CreatedUpdatedModel):
    """Privacy sensitive information on reporter."""

    _signal = models.ForeignKey(
        "signals.Signal", related_name="reporters",
        null=False, on_delete=models.CASCADE
    )

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=17, blank=True)
    remove_at = models.DateTimeField(null=True)

    extra_properties = JSONField(null=True)

# TODO Rename to through model category
class Category(CreatedUpdatedModel):
    """Store Category information and Automatically suggested category."""

    _signal = models.ForeignKey(
        "signals.Signal", related_name="categories",
        null=False, on_delete=models.CASCADE
    )

    main = models.CharField(max_length=50, default='', null=True, blank=True)
    sub = models.CharField(max_length=50, default='', null=True, blank=True)
    department = models.CharField(max_length=50, default='',
                                  null=True, blank=True)
    priority = models.IntegerField(null=True)
    ml_priority = models.IntegerField(null=True)

    # machine learning properties.
    ml_cat = models.CharField(
        max_length=50, default='', blank=True, null=True)
    ml_prob = models.CharField(
        max_length=50, default='', blank=True, null=True)
    ml_cat_all = ArrayField(
        models.TextField(max_length=50, blank=True),
        null=True)
    ml_cat_all_prob = ArrayField(models.IntegerField(), null=True)

    ml_sub_cat = models.CharField(
        max_length=500, default='', blank=True, null=True)
    ml_sub_prob = models.CharField(
        max_length=500, default='', blank=True, null=True)
    ml_sub_all = ArrayField(models.TextField(
        max_length=50, blank=True), null=True)
    ml_sub_all_prob = ArrayField(models.IntegerField(), null=True)

    extra_properties = JSONField(null=True)

    def __str__(self):
        """Identifying string."""
        return '{} - {} - {} - {}'.format(
            self.main,
            self.sub,
            self.priority,
            self.created_at
        )


LEEG = ''
GEMELD = 'm'
AFWACHTING = 'i'
BEHANDELING = 'b'
AFGEHANDELD = 'o'
ON_HOLD = 'h'
GEANNULEERD = 'a'


STATUS_OPTIONS = (
    (GEMELD, 'Gemeld'),
    (AFWACHTING, 'In afwachting van behandeling'),
    (BEHANDELING, 'In behandeling'),
    (AFGEHANDELD, 'Afgehandeld'),
    (ON_HOLD, 'On hold'),
    (GEANNULEERD, 'Geannuleerd')
)


STATUS_OVERGANGEN = {
    LEEG: [GEMELD],  # Een nieuw melding mag alleen aangemaakt worden met gemeld
    GEMELD: [AFWACHTING, GEANNULEERD, ON_HOLD, GEMELD, BEHANDELING, AFGEHANDELD],
    AFWACHTING: [BEHANDELING, ON_HOLD, AFWACHTING, GEANNULEERD, AFGEHANDELD],
    BEHANDELING: [AFGEHANDELD, ON_HOLD, GEANNULEERD, BEHANDELING],
    ON_HOLD: [AFWACHTING, BEHANDELING, GEANNULEERD, GEMELD, AFGEHANDELD],
    AFGEHANDELD: [],
    GEANNULEERD: [],
}


class Status(CreatedUpdatedModel):
    """Signal status."""

    _signal = models.ForeignKey(
        "signals.Signal", related_name="statuses",
        null=False, on_delete=models.CASCADE
    )

    text = models.CharField(max_length=10000, null=True, blank=True)
    # TODO rename field to `email` it's not a `User` it's a `email`...
    user = models.EmailField(null=True, blank=True)

    target_api = models.CharField(max_length=250, null=True, blank=True)

    state = models.CharField(
        max_length=1, choices=STATUS_OPTIONS, blank=True,
        default=GEMELD, help_text='Melding status')

    extern = models.BooleanField(
        default=False,
        help_text='Wel of niet status extern weergeven')

    extra_properties = JSONField(null=True)

    class Meta:
        verbose_name_plural = "Statuses"
        get_latest_by = "datetime"

    def __str__(self):
        return str(self.text)


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
# Category declarations
#


class MainCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        # TODO
        pass


class SubCategory(models.Model):
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
                                      related_name='sub_categories',
                                      on_delete=models.PROTECT)
    code = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=255)
    handling = models.CharField(max_length=20, choices=HANDLING_CHOICES)
    departments = models.ManyToManyField('signals.Department')

    def __str__(self):
        # TODO
        pass


class Department(models.Model):
    code = models.CharField(max_length=3)
    name = models.CharField(max_length=255)
    is_intern = models.BooleanField(default=True)

    def __str__(self):
        # TODO
        pass

    @property
    def is_extern(self):
        return not self.is_intern
