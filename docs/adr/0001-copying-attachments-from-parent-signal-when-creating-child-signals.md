# Copy attachments from a parent signal (hoofdmelding) when creating new child signals (deelmeldingen)

Date: 2020-08-18
Author: David van Buiten

## Status

Draft

## Context

Image(s) hereinafter referred to as "attachment(s)".

A Signal can be split into multiple child signals (deelmeldingen). The original Signal then becomes the parent of these children (Hoofdmelding -> deelmeldingen, 1 -> n). When these children are created it must be possible to copy specific (or all) attachments from the parent.

In the current API calls it is possible to provide images for a Signal using the attachmenst V1 endpoint. This requires a post containing the files that belong to the Signal. This can be used to provide the new child with the attachments of the parent. However this is a more devious implementation therefore we need to provide an easier method to copy the attachements.

## Decision

The goal of this ADR is to copy attachments in the most easiest way possible when creating child Signals.

Therefore the current implementation of providing attachments will only be used to provide **new** attachments. *Not to copy attachments from a parent Signal!*
If a child signal needs to copy 1 or more attachments from its parent this can be done by providing the URL's of the attachments. This will only be possible when creating a child signal.

### Development

#### Bug

First there seems to be a "bug" in the attachments list endpoint for a Signal. In the "_links" the self href does not point to the detail of the attachment. Instead it points to the list endpoint of the attachments of a Signal. This should be fixed so that it points to the correct attachment. Also the detail endpoint should be working correctly (needs to be checked).

Current: 

```json
"_links": {
	"self": {
		"href": "https://api.data.amsterdam.nl/signals/v1/private/signals/1234567890/attachments"
	}
},
```

Should be:
```json
"_links": {
	"self": {
		"href": "https://api.data.amsterdam.nl/signals/v1/private/signals/1234567890/attachments/1234567890"
	}
},
```

#### V1 Signal List endpoint

This will be the same. No information will be added to this endpoint.

#### V1 Signal Detail endpoint

The response will be modified to return a list of attachment URL's. These URL's can be used to navigate to the correspondending attachment or to provide when copying attachment to a new child Signal.


Example creation of a (parent/child) signal:

GET: https://api.data.amsterdam.nl/signals/v1/private/signals/1234567890
Response:
```json
{
	"_links": { ... },
	"_display": "1234567890 - m - None - 2020-08-18T00:00:00.000000+02:00",
	"category": { ... },
	"id": 1234567890,
	"has_attachments": true,
	"location": { ... },
	"status": { ... },
	"reporter": { ... },
	"priority": { ... },
	"notes": [ ... ],
	"type": { ... },
	"source": "online",
	"text": "example",
	"text_extra": "",
	"extra_properties": [ ... ],
	"created_at": "2020-08-18T00:00:00.000000+02:00",
	"updated_at": "2020-08-18T00:00:00.000000+02:00",
	"incident_date_start": "2020-08-18T00:00:00.000000+02:00",
	"incident_date_end": null,
	"attachments": [
		"https://api.data.amsterdam.nl/signals/v1/private/signals/1234567890/attachments/1234567890",
		"https://api.data.amsterdam.nl/signals/v1/private/signals/1234567890/attachments/0987654321",
		"https://api.data.amsterdam.nl/signals/v1/private/signals/1234567890/attachments/1111111111"
	]
}
```

When creating a child signal which need to copy attachments from it's parent a couple of rules must be checked:

* The attachment URL's provided **MUST** belong to the parent signal, no URL's of other signals can be copied.
* A attachment URL can only be copied once. So providing a list of all the same URL's must result in a new signal with only 1 attachment
* The copied attachment needs to be an actual copy. Hence the name must be altered so that it will not clash with other attachments (or the original attachment)


Example creation of a child signal:

POST: http://api.data.amsterdam.nl/signals/v1/private/signals/
Request:
```json
{
	"text": "Example child",
	"text_extra": "This is an example how to copy attachments from the parent signal",
	"location": { ... },
	"category": { .. },
	"reporter": { ... },
	"created_at": "2020-08-18T00:00:00.000000+02:00",
	"updated_at": null,
	"incident_date_start": "2020-08-18T00:00:00.000000+02:00",
	"incident_date_end": null,
	"operational_date": null,
	"image": null,
	"upload": null,
	"source": "online",
	"extra_properties": [ ... ],
	"parent": 1234567890,
	"attachments": [
		"https://api.data.amsterdam.nl/signals/v1/private/signals/1234567890/attachments/1234567890",
		"https://api.data.amsterdam.nl/signals/v1/private/signals/1234567890/attachments/0987654321"
	]
}
```
Response:
```json
{
	"_links": { ... },
	"_display": "0987654321 - m - None - 2020-08-18T00:00:00.000000+02:00",
	"category": { ... },
	"id": 0987654321,
	"has_attachments": true,
	"location": { ... },
	"status": { ... },
	"reporter": { ... },
	"priority": { ... },
	"notes": [ ... ],
	"type": { ... },
	"source": "online",
	"text": "example",
	"text_extra": "",
	"extra_properties": [ ... ],
	"created_at": "2020-08-18T00:00:00.000000+02:00",
	"updated_at": "2020-08-18T00:00:00.000000+02:00",
	"incident_date_start": "2020-08-18T00:00:00.000000+02:00",
	"incident_date_end": null,
	"parent": 1234567890,
	"attachments": [
		"https://api.data.amsterdam.nl/signals/v1/private/signals/0987654321/attachments/1234567890",
		"https://api.data.amsterdam.nl/signals/v1/private/signals/0987654321/attachments/0987654321",
	]
}
```

Providing new attachments can still be added to a (child) signal using the attachments V1 "signals/v1/private/signals/<int:pk>/attachments" or "signals/v1/public/signals/<str:signal_id>/attachments".

## Consequences

When creating a new child signal it becomes easier to copy attachments from the parent signal. This is done by providing the URL's of the attachments that needs to be copied.
