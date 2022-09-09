# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam

# TODO: Make this available for the whole project
from django.forms import JSONField, modelformset_factory
from django.forms.models import BaseModelFormSet, ModelForm

from signals.apps.api.validators.json_schema import JSONSchemaValidator
from signals.apps.questionnaires.forms.widgets import PrettyJSONWidget


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
    extra_properties = JSONField(widget=PrettyJSONWidget, required=False)
    additional_validation = JSONField(widget=PrettyJSONWidget, required=False)

    def clean_extra_properties(self):
        if hasattr(self.instance.field_type_class, 'extra_properties_schema'):
            validator = JSONSchemaValidator(self.instance.field_type_class.extra_properties_schema)
            validator(self.cleaned_data['extra_properties'])
        return self.cleaned_data['extra_properties']

    def clean_additional_validation(self):
        if self.cleaned_data['multiple_answers_allowed']:
            validator = JSONSchemaValidator(self.instance.multiple_answer_schema)
            validator(self.cleaned_data['additional_validation'])
        return self.cleaned_data['additional_validation']
