**As an** administrator
**I want** to be able to define rules to route a signal to a department/entity for further processing
**so** that I don't need to manually need to route these signals

## Proposal

We would like to introduce a rule based engine that can be used for routing. The following attributes will be available to be used in the routing rules:

*Signal*
- `Location`, lat,lon position of a signal
- `Main category` (>40% matching by ML)
- `Sub category` (>40% matching by ML)
- `Reporting Time`

*Dynamic, DSL (textX, ppci)*
We would like to define a simple (Domain Specific Language) DSL where we could define expression that uses the available attributes. If the expressions evaluates to True, the routing is applied to the Signal. We need to define the following operators for the following attributes:
- `Location`, `in` `area_identifier` 
- `Main category`, `==` `main_slug`
- `Sub category`, `==` `sub_slug`
- `Reporting Time`, `>`,`<` `time`
We also need boolean operators AND and OR.

Example: `signal.location in stadswijk.oost and signal.sub_cat == subcat.eikenprocessierups`

*Fixed*

We would like to introduce a fixed rule based engine to route signals to the handline entity.
Every rule needs to evaludate the following sections:

- `Location`, define lat,lon 'in' shape (map via spatial func: ST_WITHIN(signal.location, poly))
- `Main category`, map equal to main cat
- `Sub category`, map equal to sub cat
- `Reporting Time`, define `>`, `<` and evaluate signal.reportingtime > 20:00

