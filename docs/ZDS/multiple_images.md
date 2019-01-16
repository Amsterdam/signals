# Adding multiple image support.

To be able to support multiple images some changes need to be done for the ZDS connection.

## Model.py
First of all we need to add a `foreign key` to the `CaseDocument` model. This will keep track of
what image is synced to the ZDS.

## Tasks.py
Here we need to change the `create_documents` function. Here we will need the extra parameter
`image`, just like `add_status_to_case` with the `status`, so we can filter on the `CaseDocument`
to see if it was already uploaded. (again take a look at `add_status_to_case`)

### Reverences
Also changes all the places where `create_document` is used.


## Sync_zds.py
The change here should be that all images will be looped before they are uploaded.
