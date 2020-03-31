# Signalen Informatievoorziening Amsterdam (SIA) Application Design

SIA is an application developed for and by the Amsterdam municipality. It allows
citizens to message the Amsterdam municipality with problems they spot in public
space like broken lanterns or to file complaints about things like noise from 
bars or boats (called *incidents* throughout this document). Internally SIA is
used to keep track of the follow-up to these incidents and possibly to message
the reporter with their resolution.

## About this document
This document describes some of the reasoning behind the current implementation
of the SIA backend application and goals in developing it further. We explain
the application structure, describe the conventions to adhere to, and provide an
overview of our logging and testing setup. Finally we describe the
authentication and authorization system.


## About Datapunt
Throughout this document there are references to Datapunt. Datapunt is a
department within the Amsterdam municipality that is charged with collecting
and publishing (digitally) certain municipal data sets. To this end Datapunt
retains a few software development teams. The SIA application is being developed
by one of these teams.


## Goals and design principles

* *Adhere to standard practices of the Django community.* SIA is used by several
  hundreds of civil servants and integral part of their workflow. On the order of
  1000 issues are reported each day, which means SIA is not acting at the scales
  of Google or Netflix. Because the number of requests is relatively modest we
  can be conservative in our technology choices, and we stick to Django which is
  already in use within the Amsterdam municipality. By adhering to the Django
  standards it is easier to get new programmers up to speed and contributing to
  SIA, we furthermore minimize the risk of inventing new techniques.

* *Do not edit history of incidents.* For auditing purposes we must maintain the 
  integrity of history of each signal. The general goal is to have insight in
  the actions taken to resolve an incident, and who in our organisation took
  those actions. By implication status updates should be done by appending new
  statuses and not by editing existing ones.

* *SIA is a REST application* Like the other municipality of Amsterdam developed
  systems SIA uses a REST API. External integrations happen through the core
  REST API provided by SIA. Maintenance tasks, like bulk reassignments of
  existing signals to new categories, are performed through the REST API as
  well. This ensures that 1) the SIA REST API encompasses all actions needed to
  maintain the SIA data model and and 2) all these interactions are well-tested.

* *SIA the application does not reason in terms of user groups.* Business
  rules may require elevated privileges for some group of SIA users. SIA the
  application reasons in terms of binary permissions. If a group of users needs
  elevated permissions these **will not** be assigned in code. In stead these
  will be assigned through the user management interface (currently the Django
  admin).


## Django project structure
The Django application and its test suite can be found under: ```api/app/``` in
the Github project.

### Application core
* `signals.apps.signals` This Django app maintains data integrity within SIA. It
  contains both the Django models (table definitions) and Django model managers
  to update the data in consistent ways, see below.
* `signals.apps.api` This Django app provides the REST API to SIA. This REST
  API must encompass all actions that are needed to work with SIA data. Checks
  of user permissions are performed here. 
* `signals.apps.users` SIA user management.
* `signals.apps.feedback` Django app for the feedback on resolution of reported
  issues in public space. When an email address is known for the issue reporter
  a request for feedback will be issued by SIA. *Because of tight coupling with
  the workflow within SIA this functionality will be moved to
  `signals.apps.signals` app.*
* `signals.apps.email_integrations` All outgoing emails are generated in this
  Django app.
* `signals.auth` This package contains functionality to link SIA to the
  Datapunt OAuth2 implementation.

### Custom external integrations
* `signals.apps.sigmax` This Django app provides a minimal compatibility layer
  between SIA and CityControl which communicates using SOAP calls. This Django
  app supports a small number of predefined SOAP calls and responses and is not
  intended as a generalized SOAP client. The name is derived from the company
  that develops CityControl (Sigmax).
* `signals.apps.zds` This Django app is a prototype for integration with the
  Zaak Document Services 2.0 implementation that the Vereniging van Nederlandse
  Gemeenten (an organisation of Dutch municipalities) is working on. Currently
  development is on hold, but the test suite is maintained.

### Miscellaneous
* `signals.apps.health` This Django app is used by the Datapunt server
  infrastructure to check the health of SIA.
* `signals.utils` This package provides among other things the code that writes
  CSV dumps of a selected subset of SIA data to integrate with other municipal
  systems.


## Notable components:
* The core Django models representing signals and statuses (or other signal
  properties that have a history that must be tracked) have strong dependencies
  and rules for the order in which things are updated. The custom model manager
  `signals.apps.signals.managers.SignalManager` contains an implementation of
  the update rules, and must be used to update signals. This model manager is
  available on the `signals.apps.signal.models.Signal` model as the `actions`
  attribute.
* To maintain a loose coupling (code-wise) between the various Django apps
  within SIA we use custom Django signals. These are used to notify other parts
  of the SIA application of changes to the data.
  See for instance `signals.apps.signals.managers.create_initial`.


## SIA Topics
### Authentication and Authorization
The SIA API allows full control over the incident resolution process but only
to those with sufficient permissions. This section explains the authentication
and authorization setup of SIA. 

For authentication SIA hooks into the Datapunt OAuth2 implementation. The SIA
Django application will only grant access after 1) authenticating a user through
OAuth2 with the correct identity provider (IDP), 2) checking that that user is a
known SIA user, and 3) that that user has sufficient permissions. Authentication
and authorization are thus split between the identity provider (authentication)
and the SIA Django application (authorization). This split allows user
management through the Django admin interface.

Permission checks in the REST API are implemented using Django Rest Framework's
Permission classes that in turn use normal Django permissions. As noted above,
the SIA backend application, only implements binary permissions, no user groups
are defined in code. This choice was made to keep as much of the complexity of
the Amsterdam municipal organisation out of the SIA code base and datamodel.

Related:
* Detailed description of the [SIA authorization system](sia-authorization.md)

### External integrations (SIA API)
Several external systems integrate with SIA. These integrations use the same
REST API as the back office application and maintenance scripts. Access controls
are implemented using "system users" and permissions associated with those
users. SIA does contain some SOAP protocol compatibility code, but that does not
mean that more general SOAP support is a goal of SIA development --- it is not.
For integrations with external systems SIA is the source of truth.

The REST API of SIA is still evolving as business requirements evolve. Expected
upgrades are: stricter enforcement of consistency and moving (currently manual)
system management tasks to the API as well.

### Automatic incident categorization (Machine Learning)
SIA uses a machine learning component to perform classification on incoming
incident reports. This component is not part of the Django project and its
source is not available, but it is running on Datapunt infrastructure. 

### Usage of Django Celery (Task queue)
Some actions that SIA must perform are potentially slow, and these are off-loaded
to worker processes using the Celery task queue package. The SIA Celery setup 
uses RabbitMQ as its underlying message broker. In particular sending emails and
creating tasks in the Sigmax/CityControl system are off-loaded via Celery.

### Automatic tests and Quality Assurance
Development of SIA at Datapunt uses the standard Datapunt infrastructure, which
means every commit that is pushed to Github gets built and tested. The SIA test
suite is configured to use `pytest` as a test runner, but the test suite itself
consists of standard Django style unit tests. Beyond the test suite the `flake8`
and `isort` are run to enforce code style. All these checks are kicked off using
`Tox` (https://tox.readthedocs.io/). 

The automatic tests are part of the SIA build and deploy pipeline. Every commit
that reaches the SIA acceptance or production environments had a succesfull run
through the aforementioned checks.

### Logging
SIA uses Sentry to track application errors. SIA HTTP traffic is logged in the
general Datapunt logging as well, because SIA is running on Datapunt
infrastructure.




