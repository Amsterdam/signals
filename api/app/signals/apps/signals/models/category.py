from urllib.parse import urlparse

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.urls import resolve
from django_extensions.db.fields import AutoSlugField

from change_log.logger import ChangeLogger


class CategoryManager(models.Manager):
    def get_from_url(self, url):
        _, _, kwargs = resolve((urlparse(url)).path)
        if 'slug' in kwargs and 'sub_slug' in kwargs:
            return self.get_queryset().get(slug=kwargs['sub_slug'], parent__slug=kwargs['slug'])
        else:
            return self.get_queryset().get(slug=kwargs['slug'], parent__isnull=True)


class Category(models.Model):
    HANDLING_A3DMC = 'A3DMC'
    HANDLING_A3DEC = 'A3DEC'
    HANDLING_A3WMC = 'A3WMC'
    HANDLING_A3WEC = 'A3WEC'
    HANDLING_I5DMC = 'I5DMC'
    HANDLING_STOPEC = 'STOPEC'
    HANDLING_STOPEC3 = 'STOPEC3'
    HANDLING_KLOKLICHTZC = 'KLOKLICHTZC'
    HANDLING_GLADZC = 'GLADZC'
    HANDLING_A3DEVOMC = 'A3DEVOMC'
    HANDLING_WS1EC = 'WS1EC'
    HANDLING_WS2EC = 'WS2EC'
    HANDLING_WS3EC = 'WS3EC'
    HANDLING_OND = 'ONDERMIJNING'
    HANDLING_REST = 'REST'
    HANDLING_EMPTY = 'EMPTY'
    HANDLING_LIGHTING = 'LIGHTING'
    HANDLING_GLAD_OLIE = 'GLAD_OLIE'
    HANDLING_TECHNISCHE_STORING = 'TECHNISCHE_STORING'
    HANDLING_URGENTE_MELDINGEN = 'URGENTE_MELDINGEN'
    HANDLING_3WGM = '3WGM'
    HANDLING_MARKTEN = 'HANDLING_MARKTEN'
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
        (HANDLING_WS3EC, HANDLING_WS3EC),
        (HANDLING_REST, HANDLING_REST),
        (HANDLING_OND, HANDLING_OND),
        (HANDLING_EMPTY, HANDLING_EMPTY),
        (HANDLING_LIGHTING, HANDLING_LIGHTING),
        (HANDLING_GLAD_OLIE, HANDLING_GLAD_OLIE),
        (HANDLING_TECHNISCHE_STORING, HANDLING_TECHNISCHE_STORING),
        (HANDLING_STOPEC3, HANDLING_STOPEC3),
        (HANDLING_URGENTE_MELDINGEN, HANDLING_URGENTE_MELDINGEN),
        (HANDLING_3WGM, HANDLING_3WGM),
        (HANDLING_MARKTEN, HANDLING_MARKTEN),
    )

    parent = models.ForeignKey('signals.Category',
                               related_name='children',
                               on_delete=models.PROTECT,
                               null=True, blank=True)

    # SIG-1135, the slug is auto populated using the django-extensions "AutoSlugField"
    slug = AutoSlugField(populate_from=['name', ], blank=False, overwrite=False, editable=False)

    name = models.CharField(max_length=255)

    # SIG-2397 Handling is replaced by a handling_message
    # Notice: The handling_message will be used in communication (e-mail) to the citizen
    handling = models.CharField(max_length=20, choices=HANDLING_CHOICES, default=HANDLING_REST)
    handling_message = models.TextField(null=True, blank=True)  # noqa In the migration will set the message associated by the handling code

    departments = models.ManyToManyField('signals.Department',
                                         through='signals.CategoryDepartment',
                                         through_fields=('category', 'department'))
    is_active = models.BooleanField(default=True)

    description = models.TextField(null=True, blank=True)

    questions = models.ManyToManyField('signals.Question',
                                       through='signals.CategoryQuestion',
                                       through_fields=('category', 'question'))

    logger = ChangeLogger(track_fields=('name', 'description', 'is_active', 'slo', 'handling_message', ))

    objects = CategoryManager()

    class Meta:
        ordering = ('name',)
        unique_together = ('parent', 'slug',)
        verbose_name_plural = 'Categories'

        permissions = (
            ('sia_can_view_all_categories', 'Bekijk all categorieën (overschrijft categorie rechten van afdeling)'),  # noqa SIG-2192
            ('sia_category_read', 'Inzien van categorieën'),
            ('sia_category_write', 'Wijzigen van categorieën'),
        )

    def __str__(self):
        """String representation."""
        return '{name}{parent}'.format(name=self.name,
                                       parent=" ({})".format(
                                           self.parent.name) if self.parent else ""
                                       )

    def is_parent(self):
        return self.children.exists()

    def is_child(self):
        return self.parent is not None

    def clean(self):
        super(Category, self).clean()

        if self.pk and self.slug:
            if not Category.objects.filter(id=self.pk, slug=self.slug).exists():
                raise ValidationError('Category slug cannot be changed')

        if self.is_parent() and self.is_child() or self.is_child() and self.parent.is_child():
            raise ValidationError('Category hierarchy can only go one level deep')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def is_translated(self):
        return (not self.is_active
                and self.translations.filter(new_category__is_active=True).exists())

    def translated_to(self):
        if self.is_translated():
            return self.translations.filter(
                new_category__is_active=True
            ).order_by(
                '-created_at'
            ).first().new_category
