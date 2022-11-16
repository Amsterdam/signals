# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.validators import validate_email
from django.utils import timezone

from signals.apps.my_signals.models import Token
from signals.apps.signals.models import Reporter


class Command(BaseCommand):
    help = 'Create a token for a specific reporter'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='E-mail address of the reporter to create a token for')
        parser.add_argument('--refresh', action='store_true', dest='_refresh', help='Refresh the token')

    def _pre_handle(self, **options):
        """
        Check if all given options are valid
        """
        try:
            validate_email(options['email'])
        except ValidationError as e:
            self.stderr.write(f'{", ".join(e.messages)}')
            return False

        if not Reporter.objects.filter(email__iexact=options['email']).exists():
            self.stderr.write('Reporter not found')
            return False

        self._email = options['email']
        self._refresh = options['_refresh']
        return True

    def handle(self, *args, **options):
        if not self._pre_handle(**options):
            return

        token_qs = Token.objects.filter(
            reporter_email=self._email, expires_at__gt=timezone.now()
        ).order_by(
            '-expires_at'
        )

        if token_qs.exists() and not self._refresh:
            token = token_qs.first()
        elif token_qs.exists() and self._refresh:
            token = token_qs.first()
            token.save()
        else:
            token = Token(reporter_email=self._email)
            token.save()

        self.stdout.write(f'Reporter e-mail: {token.reporter_email}')
        self.stdout.write(f'Token: {token.key}')
        self.stdout.write(f'Expires at: {token.expires_at}')
