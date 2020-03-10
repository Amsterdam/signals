# Technical Roadmap
**This document is still under review**

*about this document*
The (user facing) feature roadmap of SIA is currently not publicly available. In
this technical roadmap we document some of the longer term technical issues that
should be addressed in the SIA backend. *Note these issues are not sorted in
any particular order*


## Turn off the "V0" of the SIA REST API
SIA was built under time pressure with the benefit of hind sight, a new API was
designed and implemented referred to as "V1". The maintenance of two REST API
versions is time consuming, increases the code footprint of the SIA backend and
makes further development of SIA slower. The new authorization system of SIA
is only implemented in V1, requiring V0 to be shut down when it comes live.

## Refactor the backend implementation of the SIA business rules. 
The SIA business rules are currently checked in a number of places across the
SIA backend code. To make the code easier to reason about, and to eventually
allow this code to be configurable this logic should be put into one module that
lives somewhere below the REST interface. This would allow a significant
simplification of the Django REST Framework code within SIA, and potentially
allow other interfaces to be implemented on top of the SIA backend. Furthermore
a more configurable implementation would allow management of some of the
business rules directly by the SIA end-users (and not the development team).

## Introduce the concept of areas in SIA
Currently SIA has data on the city district of Signals/"meldingen", but when
these are missing there is no way of adding them. Since every Signal/"melding"
has associated coordinates it should be possible to retroactively enrich the
SIA data with proper city district designations. A general implementation would
allow SIA to reason about areas, for instance to allow the access to data based
on location and not just user/role/department.

## Clean up the Django migration code
SIA has used Django migrations liberally for maintenance tasks. We are now
faced with a long list of migrations that slow down tests and deployments. These
should be removed if at all possible.

## Make the SIA authentication system configurable
Currently SIA, which is used in the Amsterdam municipal context, expects certain
external services to be available. This is no problem in the production context,
but for integration testing a way of either mocking or replacing these services
so that SIA can be run self contained for tests.