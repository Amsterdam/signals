# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam

# TODO: Make this available for the whole project

from functools import partial

from django.contrib import admin
from django.contrib.admin.checks import InlineModelAdminChecks
from django.contrib.admin.options import flatten_fieldsets
from django.contrib.admin.utils import NestedObjects
from django.core.exceptions import ValidationError
from django.db import router
from django.forms import ALL_FIELDS
from django.forms.formsets import DELETION_FIELD_NAME
from django.forms.models import modelform_defines_fields
from django.utils.text import get_text_list
from django.utils.translation import gettext as _

from signals.apps.questionnaires.admin.forms import (
    NonRelatedInlineFormSet,
    non_related_inlineformset_factory
)


class NonRelatedInlineModelAdminChecks(InlineModelAdminChecks):
    """
    The admin determines if there is a relation to the parent. For this case the relation is not there in the
    traditional Django way. Therefore we overrule these 2 actions to always pass.
    """
    def _check_exclude_of_parent_model(self, obj, parent_model):
        # Returning an empty list of errors
        return []

    def _check_relation(self, obj, parent_model):
        # Returning an empty list of errors
        return []


class NonRelatedStackedInline(admin.StackedInline):
    """
    Base class for a StackedInline with no traditional relation to the parent model.
    """
    checks_class = NonRelatedInlineModelAdminChecks
    formset = NonRelatedInlineFormSet

    def get_form_queryset(self, obj):
        """
        Should be overwritten  in the actual NonRelatedStackedInline implementation
        """
        raise NotImplementedError()

    def save_new_instance(self, parent, instance):
        """
        Should be overwritten  in the actual NonRelatedStackedInline implementation
        """
        raise NotImplementedError()

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            self.update_instance(formset.instance, instance)
            instance.save()
        formset.save_m2m()

    def get_formset(self, request, obj=None, **kwargs):  # noqa: C901
        """
        Copied from the Django InlineModelAdmin but instead of the inlineformset_factory we use the
        non_related_inlineformset_factory.
        """
        if 'fields' in kwargs:
            fields = kwargs.pop('fields')
        else:
            fields = flatten_fieldsets(self.get_fieldsets(request, obj))

        exclude = [*(self.exclude or []), *self.get_readonly_fields(request, obj)]
        if self.exclude is None and hasattr(self.form, '_meta') and self.form._meta.exclude:
            exclude.extend(self.form._meta.exclude)
        exclude = exclude or None

        can_delete = self.can_delete and self.has_delete_permission(request, obj)

        queryset = self.model.objects.none()
        if obj:
            queryset = self.get_form_queryset(obj)

        defaults = {
            'form': self.form,
            'formfield_callback': partial(self.formfield_for_dbfield, request=request),
            'formset': self.formset,
            'extra': self.get_extra(request, obj),
            'can_delete': can_delete,
            'can_order': False,
            'fields': fields,
            'min_num': self.get_min_num(request, obj),
            'max_num': self.get_max_num(request, obj),
            'exclude': exclude,
            'queryset': queryset,
            **kwargs,
        }

        base_model_form = defaults['form']
        can_change = self.has_change_permission(request, obj) if request else True
        can_add = self.has_add_permission(request, obj) if request else True

        class DeleteProtectedModelForm(base_model_form):

            def hand_clean_DELETE(self):
                """
                We don't validate the 'DELETE' field itself because on
                templates it's not rendered using the field information, but
                just using a generic "deletion_field" of the InlineModelAdmin.
                """
                if self.cleaned_data.get(DELETION_FIELD_NAME, False):
                    using = router.db_for_write(self._meta.model)
                    collector = NestedObjects(using=using)
                    if self.instance._state.adding:
                        return
                    collector.collect([self.instance])
                    if collector.protected:
                        objs = []
                        for p in collector.protected:
                            objs.append(
                                # Translators: Model verbose name and instance representation,
                                # suitable to be an item in a list.
                                _('%(class_name)s %(instance)s') % {
                                    'class_name': p._meta.verbose_name,
                                    'instance': p}
                            )
                        params = {
                            'class_name': self._meta.model._meta.verbose_name,
                            'instance': self.instance,
                            'related_objects': get_text_list(objs, _('and')),
                        }
                        msg = _("Deleting %(class_name)s %(instance)s would require "
                                "deleting the following protected related objects: "
                                "%(related_objects)s")
                        raise ValidationError(msg, code='deleting_protected', params=params)

            def is_valid(self):
                result = super().is_valid()
                self.hand_clean_DELETE()
                return result

            def has_changed(self):
                # Protect against unauthorized edits.
                if not can_change and not self.instance._state.adding:
                    return False
                if not can_add and self.instance._state.adding:
                    return False
                return super().has_changed()

        defaults['form'] = DeleteProtectedModelForm

        if defaults['fields'] is None and not modelform_defines_fields(defaults['form']):
            defaults['fields'] = ALL_FIELDS

        return non_related_inlineformset_factory(self.model, save_new_instance=self.save_new_instance, **defaults)
