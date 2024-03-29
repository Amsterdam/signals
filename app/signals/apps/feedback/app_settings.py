# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
"""
Django app settings defaults for feedback app.

Note: do not edit this file for a specific deployment. Override in the project's
central settings files instead. This file serves to provide reasonable defaults
and documents what they do.
"""
# Note: prepend all settings in this file with FEEDBACK_

# Number of days after closing of an issue that feedback is still accepted.
FEEDBACK_EXPECTED_WITHIN_N_DAYS = 14
