# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam


class ContactDetailsService:
    @staticmethod
    def obscure_email(email, escape_for_markdown):
        """
        Partially obscure a email address.

        Examples:
            - test@test.com         -> t**t@***t.com
            - test.user@gmail.com   -> t*******r@****l.com
            - test.user@amsterdam.nl-> t*******r@********m.nl
            - test@tst.com          -> t**t@***.com
            - tt@tst.com            -> tt@***.com
        """
        local, domain = email.split('@')
        local = local[0].ljust(len(local)-1, '*') + local[-1]
        sd, tld = domain[:domain.rfind('.')], domain[domain.rfind('.'):]
        sd = sd[-1:].rjust(len(sd), '*') if len(sd) > 3 else ''.join(['*' for _ in range(len(sd))])
        obscured_email = f'{local}@{sd}{tld}'

        if escape_for_markdown:
            obscured_email = obscured_email.replace('*', '\\*')  # noqa escape the * because it is used in markdown
        return obscured_email

    @staticmethod
    def obscure_phone(phone, escape_for_markdown):
        """
        Partially obscure a phone number.

        Examples:
            - +31 6 12 34 56 78 -> *******678
            - +31612345678      -> *******678
            - 06 12 34 56 78    -> *******678
            - 0612345678        -> *******678
        """
        obscured_phone = phone.replace(' ', '')
        obscured_phone = obscured_phone[-3:].rjust(10, '*')

        if escape_for_markdown:
            obscured_phone = obscured_phone.replace('*', '\\*')
        return obscured_phone
