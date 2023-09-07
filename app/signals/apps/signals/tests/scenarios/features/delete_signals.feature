# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
Feature: Delete Signals
  Scenario Outline: Delete a Signal in the state Afgehandeld for x years
    Given a Signal exists in the state Afgehandeld and the state has been set <years> years ago
    When the system runs the task to delete Signals in Afgehandeld for more than 5 years
    Then the signal should have been deleted

    Examples:
    | years  |
    |  5     |
    |  6     |
    |  7     |

  Scenario Outline: Delete all Signals in the state Afgehandeld for x years
    Given <nr_of_signals> Signals exists in the state Afgehandeld and the state has been set <years> years ago
    When the system runs the task to delete Signals in Afgehandeld for more than 5 years
    Then the signals should have been deleted

    Examples:
    | nr_of_signals | years  |
    |  2            |  5     |
    |  5            |  6     |
    |  10           |  7     |

  Scenario Outline: Delete a Signal in the state Geannuleerd for x years
    Given a Signal exists in the state Geannuleerd and the state has been set <years> years ago
    When the system runs the task to delete Signals in Geannuleerd for more than 5 years
    Then the signal should have been deleted

    Examples:
    | years  |
    |  8     |
    |  9     |
    |  10    |

  Scenario Outline: Delete all Signals in the state Geannuleerd for x years
    Given <nr_of_signals> Signals exists in the state Geannuleerd and the state has been set <years> years ago
    When the system runs the task to delete Signals in Geannuleerd for more than 5 years
    Then the signals should have been deleted

    Examples:
    | nr_of_signals | years  |
    |  2            |  8     |
    |  5            |  9     |
    |  10           |  10    |

  Scenario Outline: Delete a Signal in the state Gesplitst for x years
    Given a Signal exists in the state Gesplitst and the state has been set <years> years ago
    When the system runs the task to delete Signals in Gesplitst for more than 5 years
    Then the signal should have been deleted

    Examples:
    | years  |
    |  11    |
    |  12    |
    |  13    |

  Scenario Outline: Delete all Signals in the state Gesplitst for x years
    Given <nr_of_signals> Signals exists in the state Gesplitst and the state has been set <years> years ago
    When the system runs the task to delete Signals in Gesplitst for more than 5 years
    Then the signals should have been deleted

    Examples:
    | nr_of_signals | years  |
    |  2            |  11    |
    |  5            |  12    |
    |  10           |  13    |
