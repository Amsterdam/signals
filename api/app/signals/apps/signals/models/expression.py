from django.contrib.gis.db import models


class ExpressionType(models.Model):
    class Meta:
        verbose_name = 'ExpressionsType'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=3000)

    def __str__(self):
        return self.name


class ExpressionContext(models.Model):
    CTX_POINT = 'point'
    CTX_STRING = 'str'
    CTX_NUMBER = 'number'
    CTX_TIME = 'time'
    CTX_SET = 'set'
    CTX_DICT = 'dict'
    CTX_TYPE_CHOICES = (
        (CTX_POINT, CTX_POINT),
        (CTX_STRING, CTX_STRING),
        (CTX_NUMBER, CTX_NUMBER),
        (CTX_TIME, CTX_TIME),
        (CTX_SET, CTX_SET),
        (CTX_DICT, CTX_DICT),
    )

    class Meta:
        verbose_name = 'ExpressionContext'

    identifier = models.CharField(max_length=255)
    identifier_type = models.CharField(max_length=255, choices=CTX_TYPE_CHOICES, default=CTX_NUMBER)
    _type = models.ForeignKey(ExpressionType, on_delete=models.CASCADE)

    def __str__(self):
        return self.identifier


class Expression(models.Model):
    class Meta:
        verbose_name = 'Expression'
        unique_together = ('name', '_type')
        permissions = (
            ('sia_expression_read', 'Inzien van expressies'),
            ('sia_expression_write', 'Wijzigen van expressies'),
        )
        ordering = ['pk']

    name = models.CharField(max_length=255)
    code = models.TextField()
    _type = models.ForeignKey(ExpressionType, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
