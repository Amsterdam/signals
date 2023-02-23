# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from signals.apps.services.domain.images import IsImageChecker
from signals.apps.services.domain.pdf import IsPdfChecker


class ContentCheckerFactory:
    def __call__(self, mimetype: str, file):
        if mimetype in ('image/jpeg', 'image/png', 'image/gif'):
            return IsImageChecker(file)
        elif mimetype == 'application/pdf':
            return IsPdfChecker(file)

        return None
