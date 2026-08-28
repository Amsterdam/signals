# Polling status updates

The status update feed exposes a minimal, read-only view of status changes for signals from a configured source. It is intended for integrations that need to know when a signal enters treatment or is resolved without receiving the full signal or reporter data.

## Configuration

The endpoint is disabled by default. Configure the exact values stored in `Signal.source` as a comma-separated allowlist:

```text
STATUS_UPDATE_FEED_ALLOWED_SOURCES=mobile-app
STATUS_UPDATE_FEED_MAX_PAGE_SIZE=500
```

Use a dedicated source value that is not shared by other reporting channels. A generic value such as `online` should only be enabled when the integration intentionally needs status updates for every signal using that source.
Changing the client source affects newly created signals only; existing signals keep their original source value.

Give the integration user both the existing `signals.sia_read` permission and the dedicated `signals.sia_status_updates_read` permission. Use the existing private API token authentication.

## Request

```http
GET /signals/v1/private/status-updates?source=mobile-app&after=184234&limit=500
Authorization: Bearer <token>
```

`source` is required. `after` is an optional status-event cursor and defaults to `0`. `limit` is optional and cannot exceed `STATUS_UPDATE_FEED_MAX_PAGE_SIZE`.

## Response

```json
{
  "items": [
    {
      "signal_id": "c8e4d55f-8b84-4ff0-a960-ac285c9d0d9d",
      "status": "IN_PROGRESS",
      "changed_at": "2026-07-19T12:00:00Z",
      "event_id": 184235
    }
  ],
  "next_cursor": 184235
}
```

The feed translates internal Signalen states to stable user-facing statuses:

* `b`, `ingepland`, `h`, `forward to external`, `ready to send`, `sent`, `done external`, `closure requested`, `reaction received`, and `reopened` become `IN_PROGRESS`.
* `o` becomes `RESOLVED`.
* `a` becomes `CANCELLED`.
* `m`, `i`, `reaction requested`, `send failed`, `s`, and `reopen requested` are not returned.

The page limit counts every status event for the selected source, including statuses that are not returned. An empty `items` array can therefore still have a newer `next_cursor`. Store `next_cursor` only after processing the response successfully, and keep polling until the cursor no longer changes while catching up.

The response contains no signal description, location, reporter information, internal note, or employee information. Repeating a request with the same cursor is safe; consumers should use `event_id` for deduplication.
