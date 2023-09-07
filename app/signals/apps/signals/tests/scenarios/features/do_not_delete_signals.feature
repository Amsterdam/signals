# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
Feature: Do not delete Signals
  Scenario Outline: Do not delete a Signal in the state Afgehandeld for x years
    Given a Signal exists in the state Afgehandeld and the state has been set <years> years ago
    When the system runs the task to delete Signals in Afgehandeld for more than 5 years
    Then the Signal should not have been deleted

    Examples:
    | years  |
    |  0     |
    |  1     |
    |  2     |

  Scenario Outline: Do not delete a Signal in the state Geannuleerd for x years
    Given a Signal exists in the state Geannuleerd and the state has been set <years> years ago
    When the system runs the task to delete Signals in Geannuleerd for more than 5 years
    Then the Signal should not have been deleted

    Examples:
    | years  |
    |  1     |
    |  2     |
    |  3     |

  Scenario Outline: Do not delete a Signal in the state Gesplitst for x years
    Given a Signal exists in the state Gesplitst and the state has been set <years> years ago
    When the system runs the task to delete Signals in Gesplitst for more than 5 years
    Then the Signal should not have been deleted

    Examples:
    | years  |
    |  2     |
    |  3     |
    |  4     |
