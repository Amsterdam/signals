# Signal Receivers

[back](./readme.md)

**This is SIA Amsterdam specific code**

The signal receivers are where we listen to changes on the `django signals`.
When we receive a signal we will send the needed data to the `ZDS Components`.

## create_initial_handler
The create initial handler is used when a `melding` is created. This will be the main entry point
for creating a case.
All cases that need to be created need to go via this signal.

The create initial handler will call the following tasks:
1. create_case
2. connect_signal_to_case
3. add_status_to_case
4. create_document (optional, only if an image is attached)
5. add_document_to_case (optional, only if an image is attached)


## update_status_handler
This will listen to status updates. Once there is a status update it will send the new status to
the `ZDS Components`

The update status handler will call the following tasks:
1. add_status_to_case


## add_image_handler
This will add a document to the case. This is now used since the document is oploaded seperately
from the `melding`

The add image handler will call the following tasks:
1. create_document
2. add_document_to_case
