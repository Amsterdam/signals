# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2024 Delta10 B.V.
from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r"^(?P<path>.*)$", views.download_file, name='download_file'),
]
