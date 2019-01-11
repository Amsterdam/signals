# Tasks

[back](./index.md)

Here you can find a list of tasks. In here you schould be able to find every call that will be done
to the ZRC, DRC or ZTC.

If you are missing a function here. It should be added as a function.


## get_all_statusses

This will return a list of statusses according to the zaaktype defined in the settings


## get_status

This will use get_all_statusses to get all of the statusses and match the status texts.
If a status is found it will be returned otherwise an empty dict will be returned.


## create_case

This will create a case in the ZRC of the ZDS


## connect_signal_to_case

This will connect the signal to the case. This means that you will send the singal url to the ZRC.


## add_status_to_case

Add a new status to a case in the ZRC.


## create_document

This will create a document in the DRC. The document is not connected to anything. So be carefull
when you use this function.


## add_document_to_case

This will connect a document created with `create_document` to a case `create_case`


## get_case

This will return a case


## get_documents_from_case

This will return a list of documents that are connected to the case.
This does not include the documents themself. You will need to fetch them using 'get_informatie_object'


## get_status_history

This will return a list of statusses set. This does not include the status text. That can be requested with
`get_status_type`


## get_status_type

This will return a single status_type


## get_information_object

This will return a `enkelvoudiginformatieobject` with the contents (the actual document)
