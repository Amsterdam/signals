# Models

[back](./index.md)

**This is SIA Amsterdam specific code**

The models are a way to know how far along we are with sending the needed data to the
`ZDS Components`. This will create a link between the object that we are trying to send and the
responses from the `ZDS Components`.


## CaseSignal
This is the connection between the case and the `melding`.

| Fields                       | Type             | Why |
| ---------------------------- | ---------------- | --- |
| signal                       | ForeignKey       | Connection to the 'melding` from the SIA project. |
| zrc_link                     | UrlField         | The link to the case. This way we can see if the case is created or not. |
| connected_in_external_system | BooleanField     | If the `melding` url is send to the `ZDS components`. |
| sync_completed               | BooleanField     | If the management command has other items to send over. |

## CaseStatus
This is the connection between a status and the status from SIA.

| Fields                       | Type             | Why |
| ---------------------------- | ---------------- | --- |
| case_signal                  | ForeignKey       | Connection to the 'CaseSignal`. |
| status                       | OneToOneField    | Connection to the 'status` from the SIA project. |
| zrc_link                     | UrlField         | The link to the status. This way we can see if the status is created or not. |

## CaseDocument
This is the connection between a `enkelvoudiginformatieobject` and the image from SIA.

| Fields                       | Type             | Why |
| ---------------------------- | ---------------- | --- |
| case_signal                  | ForeignKey       | Connection to the 'CaseSignal`. |
| drc_link                     | UrlField         | The link to the status. This way we can see if the status is created or not. |
| connected_in_external_system | BooleanField     | If the `enkelvoudiginformatieobject` is connected to the case. |
