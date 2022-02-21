# Email preview for a Signal transitioning to a new status

Date: 2022-02-10
Author: David van Buiten

## Status

2022-02-21 - Approved (David van Buiten)
2022-02-10 - Draft (David van Buiten)

## Context

The problem

- It is not clear to employees which mail (subject/body) is e-mailed to the
  reporter
- It is not clear to employees how the explanation that is provided when
  changing the status will end up in the e-mail to the reporter

## Decision

An endpoint is needed that is able to trigger the email actions without
sending an actual e-mail to the reporter (and make changes to the database).

The endpoint will return the subject and the HTML body in the response. And if
there is no email action to execute a 404 not found will be returned.

The endpoint: "_/signals/v1/private/signals/1/email/preview_"

To get the endpoint to trigger the correct email action a couple of query
parameters are expected.

- The *status* query parameter. This must contain a valid state as defined in
  the "_api/app/signals/apps/signals/workflow.py_". This query parameter is
  required
- The *text* query parameter. Contains the text that will be sent to the
  reporter. This query parameter is not required

## Examples

GET /signals/v1/private/signals/1/email/preview/?status=b&text=Wij%20pakken%20dit%20z.s.m.%20op

HTTP 200 OK

```json
{
    "subject": "Uw melding SIA-1",
    "body": "<!DOCTYPE html><html lang=\"nl\"><head><meta charset=\"UTF-8\"><title>Uw melding SIA-1</title></head><body><p>Geachte melder,</p><p>Op 9 februari 2022 om 13.00 uur hebt u een melding gedaan bij de gemeente. In deze e-mail leest u de stand van zaken van uw melding.</p><p><strong>U liet ons het volgende weten</strong><br />Just some text<br /> Some text on the next line</p><p><strong>Stand van zaken</strong><br />Wij pakken dit z.s.m. op</p><p><strong>Gegevens van uw melding</strong><br />Nummer: SIA-1<br />Gemeld op: 9 februari 2022, 13.00 uur<br />Plaats: Amstel 1, 1011 PN Amsterdam</p><p><strong>Meer weten?</strong><br />Voor vragen over uw melding in Amsterdam kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00 uur. Voor Weesp kunt u bellen met 0294 491 391, maandag tot en met vrijdag van 08.30 tot 17.00 uur. Geef dan ook het nummer van uw melding door: SIA-1.</p><p>Met vriendelijke groet,</p><p>Gemeente Amsterdam</p></body></html>"
}
```

--------------------------------------------------------------------------------

GET /signals/v1/private/signals/1/email/preview/

HTTP 400 Bad Request

```json
[
    "The 'status' query parameter is required"
]
```


--------------------------------------------------------------------------------

GET /signals/v1/private/signals/1/email/preview/?status=state_does_not_exists

HTTP 400 Bad Request

```json
[
    "Invalid 'status' query parameter given"
]
```

--------------------------------------------------------------------------------

GET /signals/v1/private/signals/1/email/preview/?status=ingepland

HTTP 404 Not Found

```json
{
    "detail": "No email preview available for given status transition"
}
```
