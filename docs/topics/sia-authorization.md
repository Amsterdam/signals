# Signalen Informatievoorziening Amsterdam (SIA) authorization implementation

## About this document

SIA is an application that allows citizens to notify the Amsterdam municipality
of problems in public spaces. SIA furthermore allows municipal workers and
external partners to cooperate and the resolution of these issues. Issues that
Amsterdam is notified of through SIA are categorized. Associated with each of
these categories are one or more of the municipal departments. Some categories
are handled by external partners, that must only be allowed to access the data
that is relevant to that category.

As do other municipal applications, SIA implements role based access control. In
the near future this access control will be further enhanced with a checks
based on the departments (and through departments the categories) that users of
SIA can access.

*A note on terminology: within SIA the notifications are represented by the
`Signal` Django model.*


## Data model

The SIA backend is implemented in Django, and as such has access to a number of
well tested and maintained standard components.

* users
  - users are mapped to the standard Django `User` model (with the extra
    constraint that the username is an email address)
  - associated with each user instance is a user profile that maintains a
    relation to the department the user belongs to
  - while Django allows users to gain permissions directly, the SIA API built
    on top of this does not allow these permissions
* roles
  - roles are mapped to standard Django `Group` instances
  - users gain permissions based on their roles
* permissions
  - permissions use the standard Django `Permission` class
  - The standard behavior of Django is to create "add", "change", "delete" and
    "view" permissions for each model. SIA does not
    use these standard permissions, in stead, permissions based on high level
    actions are enforced in the API. For instance, creating a Signal instance
    requires the "Can create new signals" permission. These high level SIA
    permissions are driven by the business rules that SIA must enforce.

Beyond the more or less standard use of the Django authorization system there is
a SIA specific extension. The notifications (`Signal` instances) are assigned to
categories that are managed by different departments within the Amsterdam
municipality and a number of external partners. Users are assigned to one or
more departments, and they gain access to `Signal` data through the association
of a departments and categories.

* departments
  - A SIA specific Django model that describes a municipal department and the
    categories accessible to it. Whether a department can access a given
    category and whether the department is responsible for a given category is
    modelled as a many-to-many relation with two extra boolean properties 
    `can_view` and `is_responsible`.
* categories
  - A SIA specific Django model describing what category a `Signal` instance
    belongs to. In practice the categories in SIA have a correspondence with
    the departments of the Amsterdam municipality charged with maintaining the
    public space (they are not general categories that could just be used by
    another municipality).


## Maintaining and Managing SIA Authorizations

The SIA REST API supports the management of users, roles, departments, and
categories. The SIA backoffice management interface implements the relevant
endpoints, it however does not support the creation of new categories. Creation
of a new category generally imply follow-up tasks such as retraining the
machine learning model that SIA uses and a bulk re-categorization of existing
`Signal` instances (meldingen in Dutch) to the new category. Since some of
these tasks are technical in nature and it is possible to "break" SIA by
misconfiguring it, we do not expose the ability to add new categories in the
REST API (and the management interface). 

Related:
* [Django authorization](https://docs.djangoproject.com/en/2.2/topics/auth/)


## Backend Application Layers

SIA, the Django project, is divided into several Django apps with specific
responsibilities. The description of the data model in terms of Django models is
implemented in the `signals.apps.signals` Django app. This application has the
responsibility of keeping the data consistent, and allows atomic updates to
several tables associated with `Signal` instances at once. We consider this the
base layer of the SIA application.

On top of the base layer of SIA, an REST API layer is added. This layer is
implemented in `signals.apps.api` and exposes the only way that external
systems can interact with SIA. Beyond exposing a REST API it also implements
the access control and authorization checks.


## Implementation Details

*This section assumes familiarity with Django and Django REST Framework (DRF)*

The REST API layer of SIA is based on DRF. SIA exposes an REST API endpoint that
allows `Signal` instances to be manipulated and that accepts and emits
representations of these instances. These representations are an aggregate of
several underlying database tables. Some actions require only that the data
associated with one of these tables be manipulated, but others will touch
several tables at once. 

Only one endpoint is exposed for `Signal` instances, this endpoint implements
all authorization/permission checks associated with `Signal` instances. The
standard way of checking permissions in DRF, at the `ViewSet` class level, is
not granular enough. Furthermore, we do not want permissions checks in the
data model layer. Given these constraints, the permission checks were moved
to the `Serializer` layer. That layer already translates the incoming `Signal`
representations to the relevant methods on `Signal` Model Manager.
