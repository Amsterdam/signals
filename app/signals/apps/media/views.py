# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2024 Delta10 B.V.
from datetime import timedelta
import mimetypes
import os

from django.conf import settings
from django.core import signing
from django.contrib.staticfiles.views import serve
from django.http import HttpResponse
from django.views.static import serve

signer = signing.TimestampSigner()

def download_file(request, path):
    t = request.GET.get('t')
    s = request.GET.get('s')

    if not t or not s:
        return HttpResponse('No signature provided', status=401)

    try:
        signer.unsign(f'{path}:{t}:{s}', max_age=timedelta(hours=1))
    except signing.SignatureExpired:
        return HttpResponse('Signature expired', status=401)
    except signing.BadSignature:
        return HttpResponse('Bad signature', status=401)

    if settings.DEBUG:
        response = serve(request, path, document_root=settings.MEDIA_ROOT, show_indexes=False)
    else:
        mimetype, encoding = mimetypes.guess_type(path)

        response = HttpResponse()

        if mimetype:
            response["Content-Type"] = mimetype
        if encoding:
            response["Content-Encoding"] = encoding

        response["X-Sendfile"] = os.path.join(
            settings.MEDIA_ROOT, path
        ).encode("utf8")

    return response
