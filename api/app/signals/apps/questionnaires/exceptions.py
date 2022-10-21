# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
class SessionExpired(Exception):
    pass


class SessionFrozen(Exception):
    pass


class SessionNotFrozen(Exception):
    pass


class WrongState(Exception):
    pass


class SessionInvalidated(Exception):
    pass


class WrongFlow(Exception):
    pass


class CannotFreeze(Exception):
    pass


class CycleDetected(Exception):
    pass


class MissingEmail(Exception):
    pass
