# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Delta10 B.V.
from django.shortcuts import render


def login_failure(request):
    return render(request, 'admin/oidc/login_failure.html')
