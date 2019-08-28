from django.contrib.gis.db import models


class ReportDefinition(models.Model):
    # -- report interval granularity --
    WEEK = 'WEEK'
    MONTH = 'MONTH'  # noqa
    INTERVAL = 'INTERVAL'  # noqa
    INTERVAL_CHOICES = (
        (WEEK, 'Week'),
    )
    # -- report category granularity --
    CATEGORY_ALL = 'CATEGORY_ALL'
    CATEGORY_MAIN = 'CATEGORY_MAIN'  # noqa
    CATEGORY_SUB = 'CATEGORY_SUB'  # noqa
    CATEGORY_CHOICES = (
        (CATEGORY_SUB, 'Subcategorie'),
    )
    # -- report area granularity, currently only whole town --
    AREA_ALL = 'AREA_ALL'
    AREA_STADSDEEL = 'AREA_STADSDEEL'  # noqa
    AREA_WIJK = 'AREA_WIJK'  # noqa
    AREA_BUURT = 'AREA_BUURT'  # noqa
    AREA_CHOICES = (
        (AREA_ALL, 'Overal'),
    )

    # general report stuff
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=1000)

    # granularity of report
    interval = models.CharField(max_length=255, choices=INTERVAL_CHOICES)
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES)
    area = models.CharField(max_length=255, choices=AREA_CHOICES)
