import uuid
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField, ArrayField
# from jsonfield import JSONfield


class Signal(models.Model):
    """
    Reporting object
    """
    signal_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    source = models.CharField(max_length=15, default='api')

    text = models.CharField(max_length=1000, default='')
    text_extra = models.CharField(
        max_length=1000, default='', blank=True)

    location = models.ForeignKey(
        'Location', null=False,
        related_name="signal", on_delete=models.CASCADE
    )

    status = models.ForeignKey(
        "Status", related_name="signal",
        null=False, on_delete=models.CASCADE
    )

    category = models.ForeignKey(
        "Category", related_name="signal",
        null=True, on_delete=models.CASCADE
    )

    reporter = models.ForeignKey(
        "Reporter", related_name="signal",
        null=True, on_delete=models.CASCADE
    )

    # Date of the incident.
    incident_date_start = models.DateTimeField(null=False)
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
        models.FileField(upload_to='uploads/%Y/%m/%d/'), null=True)

    extra_properties = JSONField(null=True)


class Location(models.Model):
    """All location related information
    """
    geometrie = models.PointField(name="geometrie")
    stadsdeel = models.CharField(null=True, max_length=1)
    buurt_code = models.CharField(null=True, max_length=4)
    address = JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    extra_properties = JSONField(null=True)


class Reporter(models.Model):
    """Privacy sensitive information on reporter
    """
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=17, blank=True)
    remove_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    extra_properties = JSONField(null=True)


class Category(models.Model):
    """Store Category information and Automatically suggested category
    """
    main = models.CharField(max_length=50, default='', blank=True)
    sub = models.CharField(max_length=50, default='', blank=True)
    priority = models.IntegerField(null=True)
    ml_priority = models.IntegerField(null=True)

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


class Status(models.Model):
    """Signal Status"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    text = models.CharField(max_length=1000, default='')
    user = models.EmailField(null=True)

    STATUS = (
        ('m', 'Gemeld'),
        ('i', 'In afwachting van behandeling'),
        ('b', 'In behandeling'),
        ('o', 'Afgehandeld')
    )
    state = models.CharField(
        max_length=1, choices=STATUS, blank=True,
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


class Buurt(models.Model):
    ogc_fid = models.IntegerField(primary_key=True)
    id = models.CharField(max_length=14)
    vollcode = models.CharField(max_length=4)
    naam = models.CharField(max_length=40)

    class Meta:
        db_table = 'buurt_simple'
