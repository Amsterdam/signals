# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import os

TRUE_VALUES = [True, 'True', 'true', '1']
FEATURE_FLAGS = {
    'API_DETERMINE_STADSDEEL_ENABLED': os.getenv('API_DETERMINE_STADSDEEL_ENABLED', True) in TRUE_VALUES,
    'API_TRANSFORM_SOURCE_BASED_ON_REPORTER': os.getenv('API_TRANSFORM_SOURCE_BASED_ON_REPORTER', True) in TRUE_VALUES,

    'AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_CONTAINER': os.getenv('AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_CONTAINER', False) in TRUE_VALUES,  # noqa
    'AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_EIKENPROCESSIERUPS_TREE': os.getenv('AUTOMATICALLY_CREATE_CHILD_SIGNALS_PER_EIKENPROCESSIERUPS_TREE', False) in TRUE_VALUES,  # noqa

    # Enabled the history_log based response, disables the signal_history_view based response
    'SIGNAL_HISTORY_LOG_ENABLED': os.getenv('SIGNAL_HISTORY_LOG_ENABLED', False) in TRUE_VALUES,
    'API_USE_QUESTIONNAIRES_APP_FOR_FEEDBACK': os.getenv('API_USE_QUESTIONNAIRES_APP_FOR_FEEDBACK', False) in TRUE_VALUES,  # noqa

    # Temporary added to exclude permissions in the signals/v1/permissions endpoint that are not yet implemented in
    # the frontend
    # TODO: Remove this when the frontend is updated
    'EXCLUDED_PERMISSIONS_IN_RESPONSE': os.getenv('EXCLUDED_PERMISSIONS_IN_RESPONSE',
                                                  'sia_delete_attachment_of_normal_signal,'
                                                  'sia_delete_attachment_of_parent_signal,'
                                                  'sia_delete_attachment_of_child_signal,'
                                                  'sia_delete_attachment_of_other_user').split(','),

    # Enable/disable system mail for Feedback Received
    'SYSTEM_MAIL_FEEDBACK_RECEIVED_ENABLED': os.getenv('SYSTEM_MAIL_FEEDBACK_RECEIVED_ENABLED', False) in TRUE_VALUES,  # noqa

    # Enable/disable status mail for Handled after negative feedback
    'REPORTER_MAIL_HANDLED_NEGATIVE_CONTACT_ENABLED': os.getenv('REPORTER_MAIL_HANDLED_NEGATIVE_CONTACT_ENABLED', False) in TRUE_VALUES, # noqa

    # Enable/disable only mail when Feedback allows_contact is True
    'REPORTER_MAIL_CONTACT_FEEDBACK_ALLOWS_CONTACT_ENABLED': os.getenv('REPORTER_MAIL_CONTACT_FEEDBACK_ALLOWS_CONTACT_ENABLED', True) in TRUE_VALUES, # noqa

    # Enable/disable the deletion of signals in a certain state for a certain amount of time
    'DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED': os.getenv('DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED', False) in TRUE_VALUES,  # noqa

    # Enable/Disable the "my signals" endpoint/flows (Disabled by default)
    'MY_SIGNALS_ENABLED': os.getenv('MY_SIGNALS_ENABLED', False) in TRUE_VALUES,

    # Run routing expressions again when updating signal subcategory or location
    'DSL_RUN_ROUTING_EXPRESSIONS_ON_UPDATES': os.getenv('DSL_RUN_ROUTING_EXPRESSIONS_ON_UPDATES', False) in TRUE_VALUES,
}
