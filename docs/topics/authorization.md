# Authorization and permissions

Date: 2020-10-05  
Authors: Thijs Coenen & David van Buiten  

## About this document
This document gives a high-level overview of the SIA authorization system and
the permissions it exposes. Familiarity with Django, web application
programming are assumed throughout.

## Authorization
### SIA authorization requirements
* SIA implements role based access control. What actions SIA users can take
  is controlled by their role(s).
* Data access is controlled based on the department(s) a user is associated
  with. Each department has access to or control over Signals of a certain
  category.

### Django authorization system and SIA extensions
The SIA backend is implemented in Django and uses its authorization system.
In this section we give a high level overview how Django's authorization system
was used to fulfill SIA's requirements.

* Users
  - SIA users are mapped to the standard Django `User` model with the extra
    constraint that the username is an email address.
  - Associated with each user instance is a user profile that maintains a
    relation to the department the user belongs to
  - While Django allows users to gain permissions directly, the SIA REST API
    built on top of it does not.
* Roles
  - Roles are mapped to standard Django `Group` model.
  - Users gain permissions based on their roles.
* Permissions
  - Permissions use the standard Django `Permission` model.
  - The standard behavior of Django is to create "add", "change", "delete" and
    "view" permissions for each model. SIA uses a slight modification to this
    system as documented in section ["Permissions"](#permissions).

Beyond the generic Django authorization system SIA implements data access
restrictions based on municipal department and Signal category. A user can only
access Signals whose category is accessible to that user's department. Note, a
user can be associated with multiple departments and likewise a department can
can be associated multiple categories.

* Departments
  - A SIA specific Django model that describes a municipal department and the
    categories accessible to it. Whether a department can access a given
    category and whether the department is responsible for a given category is
    modelled as a many-to-many relation with two extra boolean properties 
    `can_view` and `is_responsible`.
* Categories
  - A SIA specific Django model describing what category a `Signal` instance
    belongs to. There are main categories and subcategories in SIA, both
    represented by the same model with the latter having a non-null foreign
    key to a main category. A Signal is always assigned a subcategory.

Related:
* [Django authorization](https://docs.djangoproject.com/en/3.2/topics/auth/)

### A note on API structure
By design citizens can leave complaints about public space anonymously. Since
these complaints are made through the API part of SIA's API does not require
authentication.

The SIA API version 1 is subdivided in a public part and a private part. The
former is available without authenticating and the latter requires both
authentication and specific authorizations. Paths in the public part of the SIA
API start with `/signals/v1/public/` and those in the private part with
`/signals/v1/private/`. External systems are assigned a SIA user and use the
SIA REST API to interact with SIA.

## Permissions

**For more information about the requests and responses please read the swagger documentation.**
* [The swagger file in the project](../api/app/signals/apps/api/templates/api/swagger/openapi.yaml)
* [SIA Production API V1 specifications](https://api.data.amsterdam.nl/api/swagger/?url=/signals/swagger/openapi.yaml)

### Top level permissions

There are 2 "top level permissions" present in SIA that control access to the
REST API. Without these top level permissions a user is not
able to do anything in SIA. With these 2 "top level permissions" it is rather easy to quickly revoke
any users reading/writing permissions on the API.

- For every read (GET) action on the V1 private API at least the permission "sia_read" is needed. 
Without this permission it is not possible to retrieve any information.

- For every write (POST, PATCH, PUT, DELETE) action on the V1 private API at least the permission 
"sia_write" is needed.

### Rights based on the Department/Category

A user works for a specific department(s). A department is responsible or can view Signals in a 
specific set of categories. This ensures that a user is only able to view and/or edit Signals that 
are assigned to a Category where a department is responsible for.

To make sure a user can edit Signals additional rights are needed. These are explained per endpoint.

This functionality can be overwritten with the permission "sia_can_view_all_categories" or by making
a user a "super user".

### The "super" user

In Django it is possible to make a user a "super" user. Basically this means that this user can do
everything in the system. This is normally not used for users using the SIA API but for users that
maintain SIA and need to login to the Django admin. 

*USE WITH GREAT CARE!!!*

### V1 Private Signals

| Endpoint                               | GET | POST | PUT | PATCH | DELETE | HEAD | OPTIONS |
|----------------------------------------|:---:|:----:|:---:|:-----:|:------:|:----:|:-------:|
| /signals/v1/private/signals/           | X   | X    | -   | X     | -      | X    | X       |
| /signals/v1/private/signals/{pk}       | X   | X    | -   | X     | -      | X    | X       |
| /signals/v1/private/signals/{pk}/split | X   | X    | -   | -     | -      | X    | X       |

| codename                        | Description                                                          | Action                                      |
|---------------------------------|----------------------------------------------------------------------|---------------------------------------------|
| sia_can_view_all_categories     | Bekijk all categorieën (overschrijft categorie rechten van afdeling) | GET /signals/v1/private/signals/            |
| sia_signal_create_initial       | Melding aanmaken                                                     | POST /signals/v1/private/signals/           |
| sia_signal_change_category      | Wijzigen van categorie van een melding                               | PATCH /signals/v1/private/signals/{pk}      |
| sia_signal_change_status        | Wijzigen van status van een melding                                  | PATCH /signals/v1/private/signals/{pk}      |
| sia_signal_create_note          | Notitie toevoegen bij een melding                                    | PATCH /signals/v1/private/signals/{pk}      |
| push_to_sigmax                  | Doorsturen van een melding (THOR)                                    | PATCH /signals/v1/private/signals/{pk}      |
| sia_split (Deprecated)          | Splitsen van een melding                                             | POST /signals/v1/private/signals/{pk}/split |
| sia_signal_export               | Meldingen exporteren                                                 | N.A.                                        |
| sia_signal_report               | Rapportage beheren                                                   | N.A.                                        |

### V1 Private Categories

| Endpoint                                                             | GET | POST | PUT | PATCH | DELETE | HEAD | OPTIONS |
|----------------------------------------------------------------------|:---:|:----:|:---:|:-----:|:------:|:----:|:-------:|
| /signals/v1/private/categories/                                      | X   | -    | -   | -     | -      | X    | X       |
| /signals/v1/private/categories/{pk}                                  | X   | -    | X   | X     | -      | X    | X       |
| /signals/v1/private/terms/categories/{slug}/status-message-templates | X   | X    | -   | -     | -      | X    | X       |

| codename                        | Description                        | Action                                                                    |
|---------------------------------|------------------------------------|---------------------------------------------------------------------------|
| sia_category_read               | Inzien van categorieën             | GET /signals/v1/private/categories/ & /signals/v1/private/categories/{pk} |
| sia_category_write              | Wijzigen van categorieën           | PUT, PATCH /signals/v1/private/categories/{pk}                            |
| sia_statusmessagetemplate_write | Wijzingen van standaardteksten     | POST/signals/v1/private/terms/categories/{slug}/status-message-templates  |

### V1 Private Departments

| Endpoint                             | GET | POST | PUT | PATCH | DELETE | HEAD | OPTIONS |
|--------------------------------------|:---:|:----:|:---:|:-----:|:------:|:----:|:-------:|
| /signals/v1/private/departments/     | X   | -    | -   | -     | -      | X    | X       |
| /signals/v1/private/departments/{pk} | X   | -    | X   | X     | -      | X    | X       |

| codename                        | Description                        | Action                                                                      |
|---------------------------------|------------------------------------|-----------------------------------------------------------------------------|
| sia_department_read             | Inzien van afdeling instellingen   | GET /signals/v1/private/departments/ & /signals/v1/private/departments/{pk} |
| sia_department_write            | Wijzigen van afdeling instellingen | PUT, PATCH /signals/v1/private/departments/{pk}                             |

### V1 Private Users/Roles/Permissions

| Endpoint                             | GET | POST | PUT | PATCH | DELETE | HEAD | OPTIONS |
|--------------------------------------|:---:|:----:|:---:|:-----:|:------:|:----:|:-------:|
| /signals/v1/private/users/           | X   | X    | -   | X     | -      | X    | X       |
| /signals/v1/private/users/{pk}       | X   | -    | -   | X     | -      | X    | X       |
| /signals/v1/private/roles/           | X   | X    | X   | X     | X      | X    | X       |
| /signals/v1/private/roles/{pk}       | X   | -    | X   | X     | X      | X    | X       |
| /signals/v1/private/permissions/     | X   | -    | -   | -     | -      | X    | X       |
| /signals/v1/private/permissions/{pk} | X   | -    | -   | -     | -      | X    | X       |

| codename        | Description              | Action                                                                      |
|-----------------|--------------------------|-----------------------------------------------------------------------------|
| view_user       | Can view user(s)         | GET /signals/v1/private/users/ & /signals/v1/private/users/{pk}             |
| add_user        | Can add user(s)          | POST /signals/v1/private/users/                                             |
| change_user     | Can change user(s)       | PUT, PATCH /signals/v1/private/users/{pk}                                   |
| delete_user     | Can delete user(s)       | DELETE /signals/v1/private/users/                                           |
| view_group      | Can view group(s)        | GET /signals/v1/private/roles/ & /signals/v1/private/roles/{pk}             |
| add_group       | Can add group(s)         | POST /signals/v1/private/roles/                                             |
| change_group    | Can change group(s)      | PUT, PATCH /signals/v1/private/roles/{pk}                                   |
| delete_group    | Can delete group(s)      | DELETE /signals/v1/private/roles/{pk}                                       |
| view_permission | Can view permissions     | GET /signals/v1/private/permissions/ & /signals/v1/private/permissions/{pk} |
