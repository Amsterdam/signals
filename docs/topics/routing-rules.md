# Routing rules
The backoffice part of the Signalen application allows users to set up rules
that will take nuisance complaints and assign to them a department
and/or user. These rules are called "routing expressions" in Signalen and they
can be edited in the Django admin. These expressions allow reasoning based on
nuisance complaint location, status, and category.

The routing expressions will be invoked at the creation of a nuisance complaint
and if the correct feature flag is set, also on change of location and category.


## Running routing rules on creation of a nuisance complaint
When a complaint is created using the Signalen frontend, machine learning will
assign it a probable main and sub category and based on that category the
reporter will be shown some extra questions. The main and sub category may not
be enough information to determine who or which department should start work on
the complaint. 

To fill this gap routing expressions were added to Signalen, these are used to
assign nuisance complainta to the correct department and possibly user. Routing
rules can take into account not just the main and sub catagories, but also the
location and time of the reported nuisance. Rules are given an priority and
executed  one-by-one until a routing expression matches. At that time the
nuisance complaint is assigned and the matching stops.


## Running routing rules on updates to a nuisance complaint
Running the routing expressions only at the creation may lead to a assigned user
or department being inappropriate after updates to the complaint. It is possible
to run the routing expressions again after certain updates to the nuisance
complaint. The Signalen installation must be configured with the feature flag
... set to True. With that feature flag activated Signalen will re-evaluate the
routing expressions and possibly re-assign the nuisance complaint.

Because routing expressions act on only a subset of nuisance complaint
properties, only updates to those properties will cause a re-evaluation of the
routing expressions. In practice this means that updates to location and
category will trigger re-evaluation. As before, the routing expressions run
one-by-one and in the same order as before, stopping at the first match.

Caveat: because all rules are evaluated in order, it may be that, for instance,
a location update triggers a rule re-evaluation but the matching rule may not
use the location at all. The order in which the rules are evaluated is fixed but
can be controlled by setting the `order` property of the routing rules.


## Example of possible surprising behavior
Take the situation where we have two routing expressions. On that
assigns a complaint to department "Stadsdeelwerken" with the expression
```
sub == "Zwerf Aval"
``
and one that assign a complaint to "j.janssen@example.com" of
"CEN (Stadsdeel Centrum)" with the expression:
```
location in area."stadsdeel"."centrum"
```
Further assume that the sub category matching rule is always evaluated first
because of the way the rules are configured.

Given a complaint in sub category "Zwerf Afval" where a location update puts it
in borough (stadsdeel) Centrum, the location rule will not match because it is
still superseded by sub category rule. The nuisance complaint will still be
assigned to "Stadsdeelwerken" based on its sub category. That the trigger to
re-evaluate was a location update changes nothing to that fact.


## Glossary

| English            | Dutch   | In code  |
| ------------------ | ------- | -------- |
| nuisance complaint | melding | signal   |
| reporter           | melder  | reporter |
