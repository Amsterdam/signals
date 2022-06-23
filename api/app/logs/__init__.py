# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import copy

from typing import List, Union

from .filters import DebugQueryFilter
from .handlers import ColoredHandler
from .config import BASE_LOGGING


__all__ = ["ColoredHandler", "DebugQueryFilter", "get_configuration"]


def get_configuration(local_apps: List[str], logging_level: Union[str, int]):
    """
    This function returns a dictionary config object that can be used as the
    LOGGING environment variable.

    It will construct a logger for every app passed via the local_apps
    list parameter with the given level in the logging_level.

    :param local_apps:
    :param logging_level:
    :return:
    """

    config = copy.deepcopy(BASE_LOGGING)

    for app_name in local_apps:
        config["loggers"].update(
            {app_name: {"level": logging_level, "handlers": ["colorize"]}}
        )

    return config
