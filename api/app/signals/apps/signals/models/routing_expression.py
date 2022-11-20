# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError

from signals.apps.signals.models import Department, Expression

User = get_user_model()


class RoutingExpression(models.Model):
    # we only allow one department routing per expression
    _expression = models.OneToOneField(
        Expression,
        on_delete=models.CASCADE,
        unique=True,
        related_name='routing_department'
    )
    _department = models.ForeignKey(Department, on_delete=models.CASCADE)
    _user = models.ForeignKey(to=User, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=False)


    class Meta:
        ordering = ['order']

    def clean(self):
        super(RoutingExpression, self).clean()

        errors = {}
        if self.is_active and self._user and not self._user.is_active:
            if '_user' not in errors:
                errors.update({'_user': []})
            errors['_user'].extend(
                ValidationError(f'{self._user.username} is not active')
            )

        if self.is_active and self._user and not self._user.profile.departments.filter(id=self._department.id).exists():
            if '_user' not in errors:
                errors.update({'_user': []})
            errors['_user'].extend(
                ValidationError(f'{self._user.username} is not part of department {self._department.name}')
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(RoutingExpression, self).save(*args, **kwargs)
