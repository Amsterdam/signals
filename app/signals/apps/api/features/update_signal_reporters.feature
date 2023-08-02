# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
Feature: Updating the reporter of signal

  Background:
    Given there is a read write user
    And there is an email template with key notify_current_reporter
    And there is an email template with key verify_email_reporter
    And there is an email template with key confirm_reporter_updated

  Scenario: Update reporter phone and email of signal with reporter that has phone and email
    Given there is a signal with reporter phone number 0200000000 and email address joep@example.com
    When I create a new reporter for the signal with phone number 0200000001 and email address jan@example.com
    Then the response status code should be 201
    And the reporter with email address joep@example.com should receive an email with template key notify_current_reporter
    And the reporter with email address jan@example.com should receive an email with template key verify_email_reporter
    When I verify the token of jan@example.com
    Then the response status code should be 200
    And the reporter with email address jan@example.com should receive an email with template key confirm_reporter_updated
    And the reporter of the signal should have phone number 0200000001 and email address jan@example.com

  Scenario: Update reporter phone and email of signal with reporter that has only phone number
    Given there is a signal with reporter phone number 0200000000 and email address null
    When I create a new reporter for the signal with phone number 0200000001 and email address jan@example.com
    Then the response status code should be 201
    And the reporter with email address jan@example.com should receive an email with template key verify_email_reporter
    When I verify the token of jan@example.com
    Then the response status code should be 200
    And the reporter with email address jan@example.com should receive an email with template key confirm_reporter_updated
    And the reporter of the signal should have phone number 0200000001 and email address jan@example.com

  Scenario: Update reporter phone and email of signal with reporter that has only email address
    Given there is a signal with reporter phone number null and email address joep@example.com
    When I create a new reporter for the signal with phone number 0200000001 and email address jan@example.com
    Then the response status code should be 201
    And the reporter with email address joep@example.com should receive an email with template key notify_current_reporter
    And the reporter with email address jan@example.com should receive an email with template key verify_email_reporter
    When I verify the token of jan@example.com
    Then the response status code should be 200
    And the reporter with email address jan@example.com should receive an email with template key confirm_reporter_updated
    And the reporter of the signal should have phone number 0200000001 and email address jan@example.com

  Scenario: Update reporter phone and email of signal with reporter that has neither
    Given there is a signal with reporter phone number null and email address null
    When I create a new reporter for the signal with phone number 0200000001 and email address jan@example.com
    Then the response status code should be 201
    And the reporter with email address jan@example.com should receive an email with template key verify_email_reporter
    When I verify the token of jan@example.com
    Then the response status code should be 200
    And the reporter with email address jan@example.com should receive an email with template key confirm_reporter_updated
    And the reporter of the signal should have phone number 0200000001 and email address jan@example.com

  Scenario: Update phone and email of signal with reporter that has new state
    Given there is a signal with reporter phone number 02000000000 and email address joep@example.com
    And the signal has a reporter with state new and phone number 0200000001, email address ja@example.com and state new
    When I create a new reporter for the signal with phone number 0200000001 and email address jan@example.com
    Then the response status code should be 201
    And the reporter with email address joep@example.com should receive an email with template key notify_current_reporter
    And the reporter with email address jan@example.com should receive an email with template key verify_email_reporter
    And the reporter with email address ja@example.com should have state cancelled

  Scenario: Update phone and email of signal with reporter that has verification_email_sent state
    Given there is a signal with reporter phone number 02000000000 and email address joep@example.com
    And the signal has a reporter with state new and phone number 0200000001, email address ja@example.com and state verification_email_sent
    When I create a new reporter for the signal with phone number 0200000001 and email address jan@example.com
    Then the response status code should be 201
    And the reporter with email address joep@example.com should receive an email with template key notify_current_reporter
    And the reporter with email address jan@example.com should receive an email with template key verify_email_reporter
    And the reporter with email address ja@example.com should have state cancelled
    And the reporter with email address ja@example.com should no longer have a verification token

  Scenario: Update phone and email of signal with reporter that has cancelled state
    Given there is a signal with reporter phone number 02000000000 and email address joep@example.com
    And the signal has a reporter with state new and phone number 0200000001, email address ja@example.com and state cancelled
    When I create a new reporter for the signal with phone number 0200000001 and email address jan@example.com
    Then the response status code should be 201
    And the reporter with email address joep@example.com should receive an email with template key notify_current_reporter
    And the reporter with email address jan@example.com should receive an email with template key verify_email_reporter
    And the reporter with email address ja@example.com should have state cancelled

  Scenario: Update reporter phone of signal with reporter that has phone and email
    Given there is a signal with reporter phone number 0200000000 and email address joep@example.com
    When I create a new reporter for the signal with phone number 0200000001 and email address joep@example.com
    Then the response status code should be 201
    And the reporter with email address joep@example.com should not receive an email with template key notify_current_reporter
    And the reporter with email address joep@example.com should not receive an email with template key verify_email_reporter
    And the reporter with email address joep@example.com should receive an email with template key confirm_reporter_updated
    And the reporter of the signal should have phone number 0200000001 and email address joep@example.com
    And the reporter with email address joep@example.com should have state approved
