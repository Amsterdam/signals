# Signalen Informatievoorziening Amsterdam (SIA) Application Design
**NOTE this document still under review**

SIA is an application developed for and by the Amsterdam municipality. It allows
citizens to message the Amsterdam municipality with problems they spot in public
space like broken lanterns or to file complaints about things like noise from 
bars or boats. Internally SIA is used to keep track the follow-up to these issues
and possibly to message the reporter with their resolution.

## About this document
This document describes some of the reasoning behind the current implementation
of the SIA backend application and goals in developing it further. We explain
the application structure, describe the conventions to adhere to, and provide an
overview of our logging and testing setup. Finally we describe the
authentication and authorization system.


## About Datapunt
Throughout this document there are references to Datapunt. Datapunt is an small
organisation within the Amsterdam municipality that is charged with collecting
and publishing (digitally) certain municipal data sets. To this end Datapunt
retains a few software development teams. The SIA application is being developed
by one of the Datapunt teams.


## Goals and design principles

* *Adhere to standard practices of the Django community.* SIA is used by several
  hundreds of civil servants and integral part of their workflow. On the order of
  1000 issues are reported each day, which means SIA is not acting at the scales
  of Google or Netflix. Because the number of requests is relatively modest we
  can be conservative in our technology choices, and we stick to Django which is
  already in use within the Amsterdam municipality. By adhering to the Django
  standards it is easier to get new programmers up to speed and contributing to
  SIA, we furthermore minimize the risk of inventing new techniques.

* *Do not edit history of Signals.* For auditing purposes we must maintain the 
  integrity of history of each signal. The general goal is to have insight in the
  actions taken to resolve an issue, and who in our origanisation took those 
  actions. By implication status updates should be done by appending new statusses
  and not by editing existing ones.

* *SIA is a REST application* Like the other municipality of Amsterdam developed
  systems SIA uses a REST API. External integrations happen, preferentially,
  through the core REST API provided by SIA. This ensures that the REST API is
  well used and well tested, benefitting all users of SIA.


## Django project structure
### Application core
The Django app `signals.apps.signals` maintains the integrity of the core data
model and provides the basic REST API to that data. This REST API is the main
way of interacting with SIA, and our first choice for a point of integration
with external systems. This Django app also enforces the workflow around 
status updates to signals.

Notable components:
* The Django models defined in `signals.apps.signals.models` for the core of the
  SIA data model. Other Django apps within the project may have models but these
  are not part of the core SIA data model.
* The core Django models representing signals and statusses (or other signal
  properties that have a history that must be tracked) have strong dependencies
  and rules for the order in which things are updated. The custom model manager
  `signals.apps.signals.models.SignalManager` contains an implementation of the
  update rules, and should be used to update signals as part of the normal 
  workflow. This model manager is available on the `signals.apps.signal.models.Signal`
  model as the `actions` attribute.
* To maintain a loose coupling between the various Django apps within SIA we use
  custom Django signals. These are used to signal that a new issue was created
  (which may for instance trigger emails), that the status of a signal changed
  etc. See for instance `signals.apps.signals.models.create_initial`.
* The SIA workflow is modelled as a state machine that is implemented in terms
  of status updates. While the `SignalManager` provided API maintains integrity
  of the data model, and fires of `DjangoSignal`s for the various update events,
  it does not enforce the status update rules. These update rules are checked
  at the serializer layer, and defined in `singals.apps.signals.workflow`.


### External integrations: Sigmax/CityControl
Sigmax provides a system, CityControl, that is used to assign work to municpal
functionaries in the streets. CityControl comprises two parts. First there is
a backoffice application that SIA comminicates with to hand off signals. Second
there are handheld devices which are fed from the backoffice that show the 
individual assignments and the information sent over from SIA. In the first
implementation of the integration with CityControl issues that are handed off
will be blocked in SIA (with regards to status updates) until resolved in 
CityControl. This rule is enforced using the workflow checks described above.

Because CityControl communicates to external systems using a SOAP standard called
StUF and cannot integrate with REST APIs, we provide a minimal stand-in for a
SOAP API to SIA. This stand-in is implemented on top of DRF and supports only
predefined messages that are used by CityControl. There is no intention to
provide a full implementation of StuF in SIA. Furthermore we strive to keep 
knowledge of external systems outside the core SIA application so the integration 
with Sigmax/CityControl is implemented in a separate Django app: 
`signals.apps.sigmax`. The core application cannot have dependencies on this
Django app, but the other way is fine.


### External integrations: Emails
A number of municipal partners need integration by email, for instance because
their employees are not in the office and they need to know when citizens report
new issues or file complaints. These email integrations are implemented in their
own Django app `signals.apps.email_integrations`. This app uses the standard
Django mail functionality.


## External integrations: CSV exports
For backups to the datawarehouse SIA exports a CSV dump of the core datamodel to
an object store. There they can be picked up by other municipal users with the
correct credentials. The implementation of this CSV dump functionality is part of
the core SIA application.

## Health
The Django app `signals.apps.health` is used to monitor application health.


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

### Authentication and Authorization
The authentication system of SIA hooks into the Datapunt OAuth2 implementation.
One role in the Datapunt authentiation system (SIG/ALL) provides access to
the SIA application. The Django application itself keeps track of SIA users
and performs the authorization. Permission checks are implemented using Django
Rest Framework's Permission classes that in turn use normal Django permissions.
This allows user management through the standard Django Admin. Users that have
SIG/ALL but have no corresponding user in the SIA Django application cannot 
access protected resources.

Muncipal employees that have access to the Amsterdam IT infrastructure gain
SIG/ALL by default after logging in through a central system. Other users that
must have access to the application can be managed by the Datapunt Identity
Provider. The reason to pull user management and authorization into the SIA
application partially pragmatic; Datapunt does not want to be burdened with
the task of user management in SIA (at the time of writing there are about
1000 users). By allowing user management in SIA through the Django Admin 
we allow a few specially staff members with knowledge of the user base to
manage users.
