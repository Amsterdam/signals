# Privacy of uploaded image attachments

## Why

A resident uploads a photograph to illustrate a report, not to share hidden
camera identifiers, capture timestamps or GPS coordinates. New image attachment
writes therefore remove metadata by default, independently of whether the
uploader is anonymous, authenticated or a staff member. This is data
minimization, not a claim about a demonstrated production leak.

This does **not** anonymize visible faces, addresses, number plates, text or
information encoded in the pixels. Original filenames, captions, report
coordinates and the application's own upload timestamps remain unchanged.
PDF attachments are not sanitized by this feature.

## Write boundaries

`services.domain.image_sanitizer.sanitize_image` decodes supported images with
Pillow and encodes fresh image objects containing only pixels and explicitly
allowlisted rendering information. No original image is stored as a fallback.

`services.attachment_files` applies that policy before storage is called:

* `Attachment.file` uses a custom `FileField`/`FieldFile`: ordinary public and
  staff uploads, model assignment/replacement, manager creation, and
  `attachment.file.save()` (including `save=False`) all pass through it.
* `StoredFile.file` uses the same boundary for questionnaire illustrations,
  including copies made when forwarding a report to an external party.
* Questionnaire session uploads call the same helper before their direct
  `default_storage.save()`. Copying replies back into a report passes through
  `Attachment.file` again.

Child-report copies are sanitized on the new write, including copies of old
attachments. JPEG copies may therefore incur another encoding generation.
Metadata-only model updates do not rewrite the blob.

The field changes have state migrations but do not scan or rewrite existing
files. Existing storage keys assigned as strings, database-only updates,
historical data migrations, direct storage SDK calls and storage restores are
not uploads through these boundaries. Importers that write new image bytes must
use these fields or `sanitize_attachment` before storage; registering an
already-written path is not a sanitization operation.

Category icons (administrator-managed configuration), generated exports and
in-memory PDF image rendering are outside this attachment policy. Do not
globally wrap all storage: that would also change unrelated files and storage
backends.

### Storage route inventory

The following is a source-level trace, not a claim that every route has passed
an integration test. Run the application regressions listed in the PR on the
supported Docker/PostGIS stack before merging.

| Route | Write boundary |
| --- | --- |
| Public/staff multipart upload | `api.serializers.attachment.BaseSignalAttachmentSerializer.create` calls `Signal.actions.add_attachment`; model `save` calls the custom field before storage. Existing MIME/extension validation is unchanged. |
| Child-report and automatic child copies | `signals.managers.SignalManager._copy_attachment_no_transaction` calls `target_attachment.file.save`. A new byte copy is sanitized; the source is not overwritten. |
| Questionnaire/session upload, including reply-photo requests | `questionnaires.rest_framework.serializers.public.attachment.PublicAttachmentSerializer.create` validates and sanitizes **all** batch members before its first direct storage write. |
| Forwarding report illustrations | `questionnaires.services.forward_to_external._copy_attachments_to_attached_files` creates `StoredFile` with copied bytes, invoking its custom field. |
| Forwarded reply copied back into a report | `ForwardToExternalSessionService._copy_attachments_from_session_to_signal` creates `Attachment` with the answer's stored bytes, invoking its custom field. |
| Model creation, file assignment, replacement, or `FieldFile.save` | Both custom fields sanitize uncommitted bytes, even with `save=False`. `Attachment.save(update_fields=['file'])` persists the derived image flag and MIME type, including after a separate `FieldFile.save(save=False)`. |
| Caption/public-flag changes and committed path references | No new byte write, hence no additional JPEG encoding. A separate model save after `FieldFile.save` does not encode again. |
| Imports | The current `signals.resources` import/export resources cover configuration (categories, questions, departments, areas and routing), not citizen attachment-byte imports. A script assigning new file bytes uses the model boundary; path-only registrations, fixtures and historical migrations do not sanitize existing storage. |

There is no storage/database transaction across file services. Batch input
validation failures store no files, but later storage or database failures can
still leave **sanitized** orphan blobs, as with the existing upload flow. The
processing budgets below apply per image, not to the total number of files in a
multipart request; request-size and concurrency limits still matter.

## Metadata and rendering policy

| Input | Output and tradeoff |
| --- | --- |
| JPEG | Same format and dimensions, except for EXIF orientation. Re-encoded at quality 95 with 4:4:4 sampling, **not lossless**; size and fine detail may change. |
| PNG | Pixel data and transparency retained, including palette transparency and Pillow-supported 16-bit grayscale with a re-serialized numeric tRNS transparency key. Palette inputs may become RGBA. No promise to preserve original PNG chunk layout or all high-bit-depth color encodings. |
| GIF | Composited animation frames, timing, loop count and transparency retained. Re-encoding full frames may change palette allocation, compression and file size; composited frames with more than 256 colors can be quantized. |
| Animated PNG | Composited frames with replacement blending, timing and loop count retained. A separate default image remains outside the animation. Existing endpoint MIME allowlists remain in force; this does not broaden accepted MIME types. |
| JPEG-compatible MPO, HDR gain maps, Motion Photos | Only the decoded primary standard-range JPEG picture is kept. Secondary pictures, gain maps, video/audio and appended payloads are not copied. Native HEIC, AVIF, WebP and other unsupported image formats are not newly enabled. |

EXIF (including GPS, capture times, device details and embedded thumbnails),
XMP, IPTC, JPEG comments, PNG text, arbitrary application extensions and trailing
container bytes are not copied. EXIF orientation is applied to the pixels
before EXIF is discarded, including mirrored orientations.

Uploaded ICC profiles can themselves contain identifying/free-form information.
Valid, supported profiles are used by Pillow's LittleCMS integration to convert
pixels to sRGB, then discarded. No input ICC bytes are embedded in the output.
Invalid, oversized or unsupported profiles cause rejection rather than silent
color fallback. Missing LittleCMS support also produces a validation error.
Gamut conversion and conversion to supported output precision
can change colors. Unprofiled CMYK JPEG uses Pillow's RGB conversion.

For PNG without an ICC profile, the numeric `gAMA`, `cHRM` and `sRGB` rendering
values are re-serialized through a small allowlist; arbitrary chunk payloads
are not copied. For converted PNG, only a generated sRGB rendering intent is
written. JPEG output without a profile is intended to be interpreted as sRGB.
These rendering values are not a general-purpose metadata-preservation channel,
but this is not a defense against deliberate steganography.

## Errors and resource budgets

Malformed images, unsupported image formats, unsafe color profiles, encoder
failures and processing-limit violations raise Django `ValidationError` before
the storage write. The existing API exception handler maps these to HTTP 400.
There is no “store the original if conversion fails” path. Storage/database
failures still propagate normally. Removing the former global
`ImageFile.LOAD_TRUNCATED_IMAGES = True` override restores Pillow's default
strict decoding; truncated images previously tolerated may now be rejected.
For historical attachments, PDF image rendering explicitly loads pixels within
its existing error handler: corrupt/truncated photos are logged and skipped,
rather than aborting the entire PDF. Those photos will be absent from the PDF;
the stored originals are not changed. No per-request global decoder toggle is
used, and upload validation remains strict.

The following are **new conservative processing limits**, not previously
guaranteed upload capabilities:

| Setting/environment variable | Default | Purpose |
| --- | --- | --- |
| `IMAGE_MAX_FRAME_PIXELS` | 25,000,000 | Limits a single decoded frame while accommodating common 12/24 MP photos. |
| `IMAGE_MAX_TOTAL_PIXELS` | 50,000,000 | Limits the sum of full composited frame areas held during animation encoding. |
| `IMAGE_MAX_FRAMES` | 200 | Bounds frame traversal and encoding work for small animations. |
| `API_MAX_UPLOAD_SIZE` | Existing 20 MiB | Now also checked on input image bytes at the write boundary and on encoded output while writing the memory buffer. |

An ICC profile is additionally limited to 1 MiB. Existing MIME/extension/size
validators and Pillow decompression-bomb/text limits remain in place. Raise
budgets only after profiling representative synthetic workloads and configuring
worker memory/concurrency limits. All values should be positive.

These budgets bound accepted input/output and pixel/frame counts, **not**
wall-clock time or total process memory. 50 million RGBA pixels alone require
about 200 MB, with additional decoder, conversion, encoder and temporary-image
allocations. Processing is synchronous in the request worker and increases CPU
and peak memory versus simply storing an upload. Native codec bugs are not
eliminated by these limits. Production container limits, request throttling,
timeouts and concurrency sizing remain necessary. Load testing is a rollout
requirement, not claimed by the unit tests.

Django/web-server temporary upload buffering may hold original bytes before
application processing; this feature prevents original-image persistence through
the attachment storage paths, not all transient handling. Restrict and expire
temporary upload storage according to the deployment's retention policy.

## Dependencies and maintenance

**No new runtime dependencies and no dependency version changes.**

| Existing dependency | Role and limits |
| --- | --- |
| Pillow 12.3.0 (already pinned in runtime/test/dev lock files) | JPEG/PNG/GIF decoding and encoding, orientation handling and ICC conversion. Maintained by the upstream `python-pillow/Pillow` project; MIT-CMU license. Parsing more of each untrusted image increases exposure compared with the former header-only check. |
| Pillow's native codecs and LittleCMS | JPEG compression, PNG compression, GIF handling and color conversion. Wheels can bundle native libraries; source builds depend on the deployment's system libraries and build options. LittleCMS support must be present for profiled uploads; failures reject the upload. |
| Existing python-magic/libmagic and Django | Content sniffing, upload validation, file fields and storage. Neither is replaced or newly introduced. |

Primary references: [Pillow 12.3.0 license](https://github.com/python-pillow/Pillow/blob/12.3.0/LICENSE),
[image formats](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html),
[ImageCms](https://pillow.readthedocs.io/en/stable/reference/ImageCms.html),
[security guidance](https://pillow.readthedocs.io/en/stable/handbook/security.html)
and [upstream advisories](https://github.com/python-pillow/Pillow/security/advisories).
An existing dependency is not automatically “safe”: continue reviewing upstream
and bundled native-library advisories, lock-file updates and image provenance.
No external executable, metadata-removal service or handwritten binary parser is
introduced.

The upstream advisory review on 2026-09-07 included
[GHSA-9hw9-ch79-4vh6](https://github.com/python-pillow/Pillow/security/advisories/GHSA-9hw9-ch79-4vh6)
(ImageCms output-mode mismatch) and
[GHSA-6r8x-57c9-28j4](https://github.com/python-pillow/Pillow/security/advisories/GHSA-6r8x-57c9-28j4)
(paste/crop coordinate overflow). Both identify 12.3.0 as patched. This is not a
complete deployment vulnerability scan or a guarantee about bundled native
libraries.

## Review and rollout

Synthetic fixtures exercise metadata removal, orientation, transparency,
animation, color handling and rejection, plus application upload/storage routes.
The PR records which checks actually ran; fixture tests are not production or
performance evidence. Maintainers should explicitly agree to the new limits,
lossy JPEG/color conversion and discarded HDR/motion behavior before enabling
this in a release.

No historical cleanup, deletion command, access-policy change or opt-out is
included. Existing files remain untouched unless copied/replaced through a new
write. Any retrospective cleanup needs its own retention, consent, backup and
rollback decision.
