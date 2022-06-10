# Django management command to delete Signals

Date: 2022-05-27
Author: David van Buiten

## Status

2022-05-27 - Draft (David van Buiten)

## Context

The problem

Legally a signal should be deleted after a certain amount of time.
The rules for this are:

- A Signal is in the state "AFGEHANDELD" for more than 5 years
- A Signal is in the state "GEANNULEERD" for more than 1 year

## Decision

A Django management command to delete Signals is needed.
This command will delete all Signals (normal, parent and child) that are in the given state for at least the given days.

Meta data is stored in the signals_deleted_signal table and a log is stored in the signals_deleted_signal_log table.
The log containts the reason for the deletion and if it was an automatic deletion or manual deletion.
The meta data stored is:

- signal id
- signal UUID
- signal state
- signal state date
- signal created date
- signal assigned category
- signal deletion date
- deleted by (optional, empty means the system user)
- batch UUID (optional, the UUID that was generated when the command started)

## Examples

--------------------------------------------------------------------------------

Delete all signals that are in the state "AFGEHANDELD" for more than 5 years

```
python manage.py delete_signals o 1461

Started: 2022-05-27 08:40:47
Batch UUID: add57200-9653-446d-a012-92ed98f48474
State: o
Days: 1461
--------------------------------------------------------------------------------
Deleted Signal: #90
--------------------------------------------------------------------------------
Deleted: 1 Signal(s)
--------------------------------------------------------------------------------
Done: 2022-05-27 08:40:47
```

```
python manage.py delete_signals o 1461

Started: 2022-05-27 08:39:20
Batch UUID: a4e8ed9b-1f9f-41d1-aea3-e7769773cc7c
State: o
Days: 1461
--------------------------------------------------------------------------------
No signal(s) found that matches criteria
--------------------------------------------------------------------------------
Deleted: 0 Signal(s)
--------------------------------------------------------------------------------
Done: 2022-05-27 08:39:20
```

Delete all signals that are in the state "GEANNULEERD" for more than 1 years

```
python manage.py delete_signals a 365

Started: 2022-05-27 08:42:57
Batch UUID: 0236fd2a-1683-480b-aa96-c3265217d41b
State: a
Days: 365
--------------------------------------------------------------------------------
Deleted Signal: #91
Deleted Signal: #92
Deleted Signal: #93
--------------------------------------------------------------------------------
Deleted: 3 Signal(s)
--------------------------------------------------------------------------------
Done: 2022-05-27 08:42:57
```

```
python manage.py delete_signals a 365

Started: 2022-05-27 08:39:00
Batch UUID: 03735f0f-432e-4d2c-a09c-ac099a1bbe5e
State: a
Days: 365
--------------------------------------------------------------------------------
No signal(s) found that matches criteria
--------------------------------------------------------------------------------
Deleted: 0 Signal(s)
--------------------------------------------------------------------------------
Done: 2022-05-27 08:39:00
```

Dry run mode, will not delete any signals

```
python manage.py delete_signals a 365 --dry-run

Dry-run mode: Enabled
Started: 2022-05-27 08:38:41
Batch UUID: 3df3c142-963c-40b9-be62-91afc21544d0
State: a
Days: 365
--------------------------------------------------------------------------------
No signal(s) found that matches criteria
--------------------------------------------------------------------------------
Dry-run mode: Enabled
Deleted: 0 Signal(s)
--------------------------------------------------------------------------------
Done: 2022-05-27 08:38:41
```

Feature disabled, will not delete any signals

```
python manage.py delete_signals a 365

Feature flag "DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED" is not enabled
```