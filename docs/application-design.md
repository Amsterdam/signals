# Signalen Informatievoorziening Amsterdam (SIA) Application Design
**NOTE this document still under review**

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


## Repository layout
The current Git repository of SIA contains, both the SIA Django implementation,
as well as code and settings to run and deploy SIA.

## Django project structure
The Django application and its test suite can be found under: ```api/app/*```.

### Application core
* `signals.apps.signals` This Django app maintains data integrity within SIA. It
  contains both the Django models (table definitions) and Django model managers
  to update the data in consistent ways.
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
* `signals.apps.dashboard` This Django app, currently in prototype state,
  provides support for Dashboard visualization of SIA data.
* `signals.utils` This package provides among other things the code that writes
  CSV dumps of a selected subset of SIA data, to integrate with other municipal
  systems.


## SIA Topics
### Authentication and Authorization
The SIA API allows full control over the incident resolution process but only
to those with sufficient permissions. This section explains the authentication
and authorization setup of SIA. 

For authentication SIA hooks into the Datapunt OAuth2 implementation. Users that
have the required OAuth2 role may, after authenticating, still not be able to
access protected resources because they lack the required permissions.
SIA the Django application will only grant access if some user is known to SIA
itself, and if that user has the correct permissions. Permission checks in the
REST API are implemented using Django Rest Framework's Permission classes that
in turn use normal Django permissions. This allows user management through the
standard Django admin interface.

As noted above, SIA the backend application, only implements binary permissions,
no user groups are defined in code. This choice was made to keep as much of the
complexity of the Amsterdam municipal organisation out of the SIA code base and
datamodel.

### External integrations
Several external systems integrate with SIA. These integrations use the same
REST API as the back office application and maintenance scripts. Access controls
are implemented using "system users" and permissions associated with those
users. Access to SIA data is protected using simple read/write permissions,
soon to be extended with access permissions based on incident category.

### Automatic incident categorization (Machine Learning)
SIA uses a machine learning component to perform classification on incoming
incident reports. This component is not part of the Django project and its
source is not available, but it is running on Datapunt infrastructure.

### Extending SIA
While it may change in the future, currently the SIA backend is available as
one large Django project with embedded Django apps. The repository, furthermore,
contains both the SIA backend application and some test and deployment code.







Currently SIA is available as one large Django project. Furthermore 


 and from a Git
repository that contain


* To maintain a loose coupling (code-wise) between the various Django apps
  within SIA we use custom Django signals. These are used to notify other parts
  of the SIA application of changes to the data.
  See for instance `signals.apps.signals.managers.create_initial`.


## Notable components:
* The Django models defined in the `signals.apps.signals.models` package form
  the core of the SIA data model. Other  for the core of the
  SIA data model. Other Django apps within the project may have models but these
  are not part of the core SIA data model.
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


### External integrations
- SIA is the central system / source of truth
- REST API is the preferred way of integrating with SIA
- historically there were some other systems with other ways of integrating



## Implementation details
### Automatic tests and QA
Development of SIA at Datapunt uses the standard Datapunt infrastructure, which
means every commit that is pushed to Github gets built and tested. Standard
Django unittests cover the application code and stylechecks are performed by
the Flake8 and isort tools. All these tests are run through Tox
(https://tox.readthedocs.io/). 

Django fixtures are used in some tests to initialize the database with correct 
data, because the test suite uses Django's `TransactionTestCase` in some places
which will flush all database tables after each test run.   

### Logging setup
* Sentry
* Kibana

### Usage of Django Celery (Task queue)
Some actions that SIA must perform are potentially slow, and these are off-loaded
to worker processes using the Celery task queue package. The SIA Celery setup 
uses RabbitMQ as its underlying message broker. In particular sending emails and
creating tasks in the Sigmax/CityControl system are off-loaded via Celery.


