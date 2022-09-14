# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import base64
import io
import logging
import os

from django.core.files.storage import default_storage
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)


class DataUriImageEncodeService:
    @staticmethod
    def resize(image, max_size):
        # Consider image orientation:
        if image.width > image.height:
            # landscape
            width = max_size
            height = int((max_size / image.width) * image.height)
        else:
            # portrait
            width = int((max_size / image.height) * image.width)
            height = max_size

        return image.resize(size=(width, height), resample=Image.Resampling.LANCZOS).convert('RGB')

    @staticmethod
    def get_context_data_images(signal, max_size):
        jpg_data_uris = []
        att_filenames = []
        user_emails = []
        att_created_ats = []

        for att in signal.attachments.all():
            # Attachment is_image property is currently not reliable
            _, ext = os.path.splitext(att.file.name)
            if ext.lower() not in ['.gif', '.jpg', '.jpeg', '.png']:
                continue  # unsupported image format, or not image format

            with io.BytesIO() as buffer:
                try:
                    with default_storage.open(att.file.name) as file:
                        buffer.write(file.read())
                        image = Image.open(buffer)
                except UnidentifiedImageError:
                    # PIL cannot open the attached file it is probably not an image.
                    msg = f'Cannot open image attachment pk={att.pk}'
                    logger.warning(msg)
                    continue
                except:  # noqa:E722
                    # Attachment cannot be opened - log the exception.
                    msg = f'Cannot open image attachment pk={att.pk}'
                    logger.warning(msg, exc_info=True)
                    continue

                if image.width > max_size or image.height > max_size:
                    image = DataUriImageEncodeService.resize(image, max_size)

                if image.mode == 'RGBA':
                    image = image.convert('RGB')

                with io.BytesIO() as new_buffer:
                    new_buffer = io.BytesIO()
                    image.save(new_buffer, format='JPEG')
                    encoded = f'data:image/jpg;base64,{base64.b64encode(new_buffer.getvalue()).decode("utf-8")}'

            att_filename = os.path.basename(att.file.name)

            jpg_data_uris.append(encoded)
            att_filenames.append(att_filename)
            user_emails.append(att.created_by)
            att_created_ats.append(att.created_at)

        return jpg_data_uris, att_filenames, user_emails, att_created_ats
