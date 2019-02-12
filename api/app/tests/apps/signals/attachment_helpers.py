import os

from django.core.files.uploadedfile import SimpleUploadedFile

from signals.apps.signals.models import Attachment

small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


def add_non_image_attachments(signal, n=1):
    """ Adds n file attachments to signal. Returns added attachments """
    doc_upload_location = os.path.join(os.path.dirname(__file__), 'sia-ontwerp-testfile.doc')
    attachments = []

    for _ in range(n):
        with open(doc_upload_location, "rb") as f:
            doc_upload = SimpleUploadedFile("file.doc", f.read(),
                                            content_type="application/msword")

            attachment = Attachment()
            attachment.file = doc_upload
            attachment._signal = signal
            attachment.save()
            attachments.append(attachment)

    return attachments


def add_image_attachments(signal, n=1):
    """ Adds n image attachments to signal. Returns added attachments """
    attachments = []

    for _ in range(n):
        image = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
        attachment = Attachment()
        attachment.file = image
        attachment._signal = signal
        attachment.save()
        attachments.append(attachment)

    return attachments
