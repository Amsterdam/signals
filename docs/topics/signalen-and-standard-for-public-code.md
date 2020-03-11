# Signalen and the Standard for Public Code

## [Code in the open](https://standard.publiccode.net/criteria/code-in-the-open.html)

* Current backlog and bug-tracking is not public. Some issues referenced in code and commits are not easy to locate, like "SIG-1525". Transition to public bug-tracker?
* Can the classification system be completely open sourced? How can we address risks and possibilities regarding (of theoretical) leaking of information. Maybe add anonymized MOR datasets or redo the classification algorithm with public available MOR data sets. Can a basic Common Ground version be made?

## [Bundle Policy And Source Code](https://standard.publiccode.net/criteria/bundle-policy-and-code.html)

* Making the business rules and the associated state machine configurable. This would enable SIA to adapt to policy changes within Amsterdam and also makes it easier for replicators to customise SIA for their policy/workflows.

## [Create reusable and portable code](https://standard.publiccode.net/criteria/reusable-and-portable-codebases.html)

* There are several dependencies on Amsterdam services. Replicators need this to be configurable.
* Technical roadmap is not published.
* [Workflow](https://github.com/Amsterdam/signals/blob/master/api/app/signals/apps/signals/workflow.py) is currently hard-coded. Names of key states can be found elsewhere, need abstraction plan.
* Email messages are [hard-coded](https://github.com/Amsterdam/signals/blob/master/api/app/signals/apps/email_integrations/core/messages.py).
* Separate UI text from API model classes: [example](signals/api/app/signals/apps/signals/models/history.py).
* Extended category questions currently live in front-end code, extract and make plug-able.

## [Welcome contributors](https://standard.publiccode.net/criteria/open-to-contributions.html)

* Improve [CONTRIBUTING.md](https://github.com/Amsterdam/signals/blob/master/docs/CONTRIBUTING.md), perhaps with content from Amsterdam's [CONTRIBUTING.md](https://github.com/Amsterdam/amsterdam.github.io/blob/master/CONTRIBUTING.md)

## [Maintain version control](https://standard.publiccode.net/criteria/version-control-and-history.html)

* Good.
    * Some past commits did not state what they do or why, some just reference an issue, or have "[WIP](https://github.com/Amsterdam/signals/commit/2f9e2f73ee5dc4cdf67d6854d1a7361f6e6aaf9b)" commit messages; developers have become more rigorous.

## [Require review of contributions](https://standard.publiccode.net/criteria/require-review.html)

* Ensure commits are reviewed including commit message.

## [Document your objectives](https://standard.publiccode.net/criteria/document-objectives.html)

* Feature roadmap is not published.
* Improve goals documented in README to include information on scope, purposes, and reasoning.

## [Use plain English](https://standard.publiccode.net/criteria/understandable-english-first.html)

* Translate the Dutch-only documentation and text in code, so it is also available in English.
* Ensure dutch names, messages, words in code are localizable.

## [Use open standards](https://standard.publiccode.net/criteria/open-standards.html)

* Good.

## [Use continuous integration](https://standard.publiccode.net/criteria/continuous-integration.html)

* Tests not currently invoked by Travis or similar public continuous integration. (Tests are run in the Datapunt CI)
* Running tests locally is documented in the [README](https://github.com/Amsterdam/signals/blob/master/README.md#running-the-test-suite-and-style-checks)
* No clear integration testing or capacity testing.
* Code coverage by tests is not published.
* Ensure test fixtures are separated from production code.

## [Publish with an open license](https://standard.publiccode.net/criteria/open-licenses.html)

* Good.
    * License: [Mozilla Public License Version 2.0](../../LICENSE)

## [Use a coherent style](https://standard.publiccode.net/criteria/style.html)

* Conforms to the PEP8 style guide, and is automatically checked.

## [Pay attention to codebase maturity](https://standard.publiccode.net/criteria/advertise-maturity.html)

* Migration to current REST API still in progress, completion status not currently published.
* Publish plans/goals of next revision of the REST API.
