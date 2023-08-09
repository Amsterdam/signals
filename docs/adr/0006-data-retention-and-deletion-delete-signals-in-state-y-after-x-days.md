# Data retention and deletion - Delete Signals in state Y after X days

Date: 2023-08-09
Author: David van Buiten

## Status

2023-08-09 - Final (David van Buiten)

## Context

In compliance with the Dutch [Archiefwet](https://www.amsterdam.nl/privacy/loket/privacyverklaring-loket-persoonsgegevens/),
the municipality is obligated to delete signals with a final status after a specified period.

Signals that have been canceled should be destroyed after 1 year, while signals marked as resolved should
be deleted after 5 years.

Signals that have been historically split should also be removed, including their child signals.

The same principles apply to parent and child signals (deelmeldingen).

When referring to the deletion of a signal, the following actions are implied:

1. The signal is completely removed from the database
2. All links to other tables are severed (e.g., category_assignments need to be removed, but the categories themselves remain unaffected)
3. Attached photos/pdf's (attachments) are also deleted

The following information (meta data) should be recorded:

- Signal ID
- Signal UUID
- Parent Signal ID (if present)
- Signal State
- Signal State set at
- Signal Category
- Signal Created at
- Reason for Deletion (automated or manual, in this case, "automated")
- Deleted by (A user or the system)
- Date of Deletion
- Batch UUID

These details will be recorded in a table to track the deleted signals:

| Signal ID | Signal UUID | Parent Signal ID | Signal State | Signal State set at | Signal Category | Signal Created at | Reason for Deletion | Deleted by | Date of Deletion | Batch UUID |
|-----------|-------------|------------------|--------------|---------------------|-----------------|-------------------|---------------------|------------|------------------|------------|
|           |             |                  |              |                     |                 |                   |                     |            |                  |            |

The objective is to establish a method for automating the periodic deletion of these signals, similar to the
existing process of anonymization.

## Decision

In order to implement the data retention and deletion process as outlined in the Context chapter, the following
decisions have been made:

### Signal Deletion Service

A `SignalDeletionService` will be developed to manage the deletion of signals based on the specified criteria.
This service will handle the automated deletion of signals that have met the retention requirements. The
`SignalDeletionService` will incorporate the following features:

- Delete signals and child signals in a given state and older than a specified number of days.
- Check preconditions such as feature flag settings, valid states, days, and signal ID.
- Select and retrieve signals for deletion based on specified criteria.
- Delete signals and associated data, including child signals and attachments.
- Log deletion details in a `DeletedSignal` table for reporting purposes.
- Remove signals from the Elasticsearch index using the `delete_from_elastic` function.

### Django Management Command

A Django management command, named `delete_signals`, will be created to allow administrators to trigger the data
deletion process manually. The command will take the following arguments:

- `state`: The state a signal must be in to be deleted, with available choices being "AFGEHANDELD," "GEANNULEERD," or "GESPLITST."
- `days`: The minimum number of days a signal must be in the given state to be eligible for deletion.
- `--signal-id`: (Optional) The ID of a specific signal to delete.
- `--dry-run`: (Optional) Flag to enable dry-run mode, where no actual deletions are performed.

The `delete_signals` management command will make use of the `SignalDeletionService` to execute the deletion process,
and it will provide feedback on the actions taken.

### Celery Task

To further enhance the data retention and deletion process, a Celery task should be implemented. This task will allow
the deletion process to be executed asynchronously, reducing the impact on system performance during deletion
operations. The Celery task will be responsible for scheduling and executing the data deletion process based on the
specified criteria. The exact implementation details of this Celery task need to be developed.
