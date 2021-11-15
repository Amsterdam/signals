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

    def clean(self):
        super(RoutingExpression, self).clean()

        errors = {}
        if self._user and not self._user.profile.departments.filter(id=self._department.id).exists():
            errors.update({
                '_user': ValidationError(f'{self._user.username} is not part of department {self._department.name}')
            })

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(RoutingExpression, self).save(*args, **kwargs)

    # objects = models.Manager()

    # def save(self, *args, **kwargs):
    #     if not self.validate_user():
    #         raise ValidationError(f'{self.user.username} is not part of department {self._department.name}')
    #
    #     super(RoutingExpression, self).save(*args, **kwargs)

    # def validate_user(self):
    #     """
    #     If a User is set it MUST belong to the set Department
    #     If no User is set return True, no need to check if None is a member of the set Department.
    #     """
    #     if not self._user:
    #         return True  # No need to check if the user is a member of the department because no user is given
    #
    #     # Check if the user is a member of the given department
    #     return self._user.profile.departments.filter(id=self._department.id).exists()
