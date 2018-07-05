import uuid
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField, ArrayField


class Buurt(models.Model):
    ogc_fid = models.IntegerField(primary_key=True)
    id = models.CharField(max_length=14)
    vollcode = models.CharField(max_length=4)
    naam = models.CharField(max_length=40)

    class Meta:
        db_table = 'buurt_simple'


class Signal(models.Model):
    """
    Reporting object
    """

    def __init__(self, *args, **kwargs):
        super(Signal, self).__init__(*args, **kwargs)
        if not self.signal_id:
            self.signal_id = uuid.uuid4()

    # we need an unique id for external systems.
    signal_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    source = models.CharField(max_length=15, default='api')

    text = models.CharField(max_length=1000)

    text_extra = models.CharField(
        max_length=1000, default='', blank=True)

    location = models.OneToOneField(
        'Location', related_name="signal",
        null=True, on_delete=models.CASCADE
    )

    status = models.OneToOneField(
        "Status", related_name="signal",
        null=True, on_delete=models.CASCADE
    )

    category = models.OneToOneField(
        "Category", related_name="signal",
        null=True, on_delete=models.CASCADE
    )

    reporter = models.OneToOneField(
        "Reporter", related_name="signal",
        null=True, on_delete=models.CASCADE
    )

    # Date of the incident.
    incident_date_start = models.DateTimeField(null=False, auto_now_add=True)
    incident_date_end = models.DateTimeField(null=True)
    created_at = models.DateTimeField(null=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    # Date action is expected
    operational_date = models.DateTimeField(null=True)
    # Date we should have reported back to reporter.
    expire_date = models.DateTimeField(null=True)
    image = models.ImageField(
        upload_to='images/%Y/%m/%d/', null=True, blank=True)

    # file will be saved to MEDIA_ROOT/uploads/2015/01/30
    upload = ArrayField(
        models.FileField(
                upload_to='uploads/%Y/%m/%d/'), null=True)

    extra_properties = JSONField(null=True)

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


STADSDELEN = (
    ('A', 'Centrum'),
    ('B', 'Westpoort'),
    ('E', 'West'),
    ('M', 'Oost'),
    ('N', 'Noord'),
    ('T', 'Zuidoost'),
)


def get_buurt_code_choises():
    return Buurt.objects.values_list('vollcode', 'naam')


class Location(models.Model):
    """All location related information
    """

    _signal = models.ForeignKey(
        "Signal", related_name="signals",
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
                if field in self.address:
                    address_text += prefix + self.address[field]
            self.address_text = address_text

    def save(self, *args, **kwargs):
        # Set address_text
        self.set_address_text()
        super().save(*args, **kwargs)  # Call the "real" save() method.


class Reporter(models.Model):
    """Privacy sensitive information on reporter
    """

    _signal = models.ForeignKey(
        "Signal", related_name="reporters",
        null=False, on_delete=models.CASCADE
    )

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=17, blank=True)
    remove_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    extra_properties = JSONField(null=True)


class Category(models.Model):
    """Store Category information and Automatically suggested category
    """

    _signal = models.ForeignKey(
        "Signal", related_name="categories",
        null=False, on_delete=models.CASCADE
    )

    main = models.CharField(max_length=50, default='', null=True, blank=True)
    sub = models.CharField(max_length=50, default='', null=True, blank=True)
    department = models.CharField(max_length=50, default='', null=True, blank=True)
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    extra_properties = JSONField(null=True)

    def __str__(self):
        """Identifying string.
        """
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
    GEMELD: [AFWACHTING, GEANNULEERD, ON_HOLD, GEMELD],
    AFWACHTING: [BEHANDELING, ON_HOLD, AFWACHTING, GEANNULEERD],
    BEHANDELING: [AFGEHANDELD, GEANNULEERD, BEHANDELING],
    ON_HOLD: [AFWACHTING, BEHANDELING, GEANNULEERD],
    AFGEHANDELD: [],
    GEANNULEERD: [],
}


class Status(models.Model):
    """Signal Status

    Updates / Changes are handeled here
    """

    _signal = models.ForeignKey(
        "Signal", related_name="states",
        null=False, on_delete=models.CASCADE
    )

    text = models.CharField(max_length=1000, default='')
    user = models.EmailField(null=True)

    target_api = models.CharField(max_length=250, default='')

    state = models.CharField(
        max_length=1, choices=STATUS_OPTIONS, blank=True,
        default='m', help_text='Melding status')

    extern = models.BooleanField(
        default=False,
        help_text='Wel of niet status extern weergeven')

    created_at = models.DateTimeField(
        auto_now_add=True, null=False, db_index=True)
    updated_at = models.DateTimeField(
        auto_now_add=True, null=True, db_index=True)

    extra_properties = JSONField(null=True)

    class Meta:
        verbose_name_plural = "States"
        get_latest_by = "datetime"

    def __str__(self):
        return self.text
