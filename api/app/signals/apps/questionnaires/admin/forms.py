# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam

# TODO: Make this available for the whole project

from django.forms import modelformset_factory
from django.forms.models import BaseModelFormSet, ModelForm

from signals.apps.api.validators.json_schema import JSONSchemaValidator


class NonRelatedInlineFormSet(BaseModelFormSet):
    """
    A basic implementation of an inline formset that doesn't make assumptions
    about any relationship between the form model and its parent instance.
    """
    def __init__(self, instance=None, save_as_new=None, **kwargs):
        self.instance = instance
        super().__init__(**kwargs)
        self.queryset = self.real_queryset

    @classmethod
    def get_default_prefix(cls):
        return cls.model._meta.app_label + '-' + cls.model._meta.model_name

    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        self.save_new_instance(self.instance, obj)
        if commit:
            obj.save()
        return obj


def non_related_inlineformset_factory(model, obj=None, queryset=None, formset=NonRelatedInlineFormSet,
                                      save_new_instance=None, **kwargs):
    FormSet = modelformset_factory(model, formset=formset, **kwargs)
    FormSet.real_queryset = queryset
    FormSet.save_new_instance = save_new_instance
    return FormSet


class QuestionAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self.instance.field_type_class, 'extra_properties_schema'):
            # Let's add the extra properties validator to the form
            self.fields['extra_properties'].required = True
            self.fields['extra_properties'].empty = False
            self.fields['extra_properties'].validators.append(
                JSONSchemaValidator(self.instance.field_type_class.extra_properties_schema)
            )
        else:
            # Extra properties are not required so disable the field
            self.fields['extra_properties'].required = False
            self.fields['extra_properties'].disabled = True
