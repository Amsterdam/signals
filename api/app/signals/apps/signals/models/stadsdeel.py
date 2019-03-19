from django.contrib.gis.db import models


class Stadsdeel(models.Model):
    ogc_fid = models.IntegerField(primary_key=True)
    id = models.CharField(max_length=14)
    code = models.CharField(max_length=1)
    naam = models.CharField(max_length=40)
    wkb_geometry = models.PolygonField(srid=4326, null=True)

    class Meta:
        db_table = 'stadsdeel'
