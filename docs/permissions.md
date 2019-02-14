# SIA Permissions

## SIA_BACKOFFICE and category permissions


The v1 API offers the opportunity to give users permissions to only read
and update signals from certain categories. This is implemented for
connecting with external parties, who should only have access to certain
types (categories) of signals. Nothing stops the application
administrators to use category permissions for other users as well.

### How does this work?
#### V0 API
In the V0 API, all users should have - besides the other permissions
they need to do their job - the SIA_BACKOFFICE permission. It is not
possible to use the V0 API without the SIA_BACKOFFICE permission.

#### V1 API
Users can access the V1 API either with or without the SIA_BACKOFFICE
permission. In case the SIA_BACKOFFICE permission is present, no
restrictions are placed on the categories from which the user can access
signals. If the user is NOT assigned the SIA_BACKOFFICE permission, the
user only has access to the categories he/she has access to. This is
controlled with the "category permissions", which can be assigned
through the Django admin.

### But, what are those restrictions on categories?
A user needs access to a category:
- To retrieve a signal from that category
- To update a signal from that category
- To move a signal to that category
- To see signals from that category on the GET /signals endpoint. (In
other words, we filter the result set to only keep signals the user
has access to).

It follows that a user WITHOUT the SIA_BACKOFFICE permission and NO
category permissions will see an empty list on GET /signals, is unable
to retrieve any signal on GET /signals/{id} and is unable to update any
signal.

### And now, a bit more technical?
#### Generation of category permissions
The permissions are created in the ```apps/signals/permissions.py```
file. The ```CategoryPermissions.create_for_all_categories()``` method
is called every time the admin group or user page is loaded. The hooks
for this are in ```apps/users/admin.py```. This makes sure that whenever
an administrator wishes to assign category permissions to a user or
group, the list is up-to-date.

#### Enforcing the permissions
Enforcing the category permissions is done in
```apps/signals/v1/views.py```. The private ViewSet classes inherit from
the ```PrivateSignalViewSetBase``` class, that handles filtering the
queryset and throwing the appropriate 403/404's on a call to
```get_object```, which is used on the detail endpoints. Additional
information is added in comments in the code.

Prevention of moving signals to a forbidden category is done in the
```validate()``` method of ```PrivateSignalSerializerDetail``` in
```apps/signals/v1/serializers.py```.

