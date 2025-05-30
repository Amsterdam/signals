# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.

from django import forms
from .models import ForwardToExternal, SetState
from markdownx.widgets import AdminMarkdownxWidget


class ForwardToExternalModelForm(forms.ModelForm):
    class Meta:
        model = ForwardToExternal
        fields = '__all__'
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }


class SetStateModelForm(forms.ModelForm):
    class Meta:
        model = SetState
        fields = '__all__'
        widgets = {
            'text': AdminMarkdownxWidget,
        }
