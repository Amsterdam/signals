# Copy attachments from a parent signal (hoofdmelding) when creating new child signals (deelmeldingen)

Date: 2020-08-18
Author: David van Buiten & Thijs Coenen

## Status

Draft

## Context

SIA deals with complaints to a municipality about problems in public spaces. In
SIA jargon these complaints are "signals". Signals often contain several
complaints or have to be handled by multiple municipal departments. To
accommodate these signals in the complaint resolution workflow SIA allows signals
to be split into several "child signals" (deelmeldingen) whilst the original
signal becomes a "parent signal" (hoofdmelding).

As part of a larger effort to overhaul the handling of these complex complaints
attachment handling must be addressed. Outside the scope of this ADR, but
relevant to it, is the decision to allow creation of child signals in batches.
This ADR describes how attachments can be copied from a parent signal to child
signals upon their creation.

Functional goals:
- when a child signal is created it must be possible to specify one or more
  of the parent's attachments to copy to the child signal

In the current API an attachment endpoint is associated with each signal.
Uploading an file to that endpoint links that file to the signal as an
attachment. This mechanism, in principle, can be re-used to provide child
signals with specific attachments from its parent. However it is not a
convenient mechanism --- nor is it robust.

Problems with the status quo:
- A client needs to keep state during the creation of child signals and
  uploading of attachments. Losing network connection or internal state will
  leave the child signals in an "unfinished" state.
- Downloading and re-uploading attachments uses a large amount of bandwidth and
  is time consuming.

Having thus described the goal of this ADR and problems with the current
approach we propose the following, secondary, design goals:
- API clients should not have to re-upload attachments (i.e. conserve bandwidth)
- API clients should be able to create child signals with a minimum of API
  requests (i.e. maintain consistency in case the network or client issues)
- the API should maintain backwards compatibility

## Decision

The current upload mechanism will only be used to provide *new* attachments, not
to copy attachments from a parent signal upon the creation of a child signal.
In stead, when a child signal is created its attachments can be set by providing
the URLs to zero, one or more of the parent's attachments. This requires the
following changes to the API:

- it must be possible to uniquely identify an attachment through a path in
  the API
- it must be possible to provide these attachment URLs when a child signal is
  created

What follows below is a more detailed description of the proposed changes.

### Development

#### Bug

First there seems to be a "bug" in the attachments list endpoint for a Signal. 
In the "_links" the self href does not point to the detail of the attachment. 
Instead it points to the list endpoint of the attachments of a Signal. This
must be fixed so that an attachment can be uniquely identified. An
implementation must also be provided for the attachment detail endpoint, as it
currently does not exist.

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

This latter URL points to the, as yet unimplemented, attachment detail endpoint.

#### V1 Signal List endpoint

No changes will be made to the output of this endpoint because exposing more
information here will further slow down an already slow endpoint. Note that upon
creation of a batch of child signals the response will contain a serialization
of these child signals.

#### V1 Signal Detail endpoint

The response will be modified to return a list of attachment URL's. These URL's
can be used to navigate to the corresponding attachment or to provide when 
copying attachment to a new child Signal. As an aside: the attachments list
endpoint will remain available so it will remain possible to retrieve all
attachments associated with a signal in one API request.

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
		"https://api.data.amsterdam.nl/signals/v1/private/signals/1234567890/attachments/1987654321",
		"https://api.data.amsterdam.nl/signals/v1/private/signals/1234567890/attachments/1111111111"
	]
}
```

When creating a child signal which need to copy attachments from its parent a
couple of rules must be obeyed:

- The attachment URLs provided **MUST** belong to the parent signal.
- A attachment URL can only be copied once. Repeating the same URL must result
  in a new signal with only one copy of that attachment.
- Given the underlying data model and the desire to have simple access rules the
  copied attachment will to be an actual copy. This implies that the final URLs
  child signal attachments URLs will be different from the ones provided.

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
		"https://api.data.amsterdam.nl/signals/v1/private/signals/1234567890/attachments/987654321"
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
		"https://api.data.amsterdam.nl/signals/v1/private/signals/0987654321/attachments/5234567890",
		"https://api.data.amsterdam.nl/signals/v1/private/signals/0987654321/attachments/4987654321",
	]
}
```

Providing new, not previously uploaded, attachments can still be done. In that
case a POST containing the new file to the attachment list endpoint of a signal
will suffice.

 to a (child) signal using the attachments V1 "signals/v1/private/signals/<int:pk>/attachments" or "signals/v1/public/signals/<str:signal_id>/attachments".

## Consequences

This ADR provides a way of creating child signals with attachments copied from
their parents in an efficient way. It will be possible to use the batch creation
of child signals mechanism to also copy attachments from their parents.

All goals, described in the context section, are met save the backwards
compatibility goal. The proposed change is, strictly speaking, incompatible
because it changes the output of the attachments list endpoint to give each
attachment a unique path in the API. In our estimation this is of no consequence
because the current behavior can be considered a bug.
