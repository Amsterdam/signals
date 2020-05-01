from django.contrib.gis.db import models


class AreaType(models.Model):
    class Meta:
        verbose_name = 'Gebiedstype'
        verbose_name_plural = 'Gebiedstypen'

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    description = models.TextField(max_length=3000)

    def __str__(self):
        return self.name


class Area(models.Model):
    class Meta:
        verbose_name = 'Gebied'
        verbose_name_plural = 'Gebieden'

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    _type = models.ForeignKey(AreaType, on_delete=models.CASCADE)
    geometry = models.MultiPolygonField()

    def __str__(self):
        return self.name
