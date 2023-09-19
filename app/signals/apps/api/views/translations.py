# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import json
import mimetypes

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import FileResponse
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from signals.apps.api.generics.permissions import CanCreateI18NextTranslationFile
from signals.auth.backend import JWTAuthBackend


class PrivateCreateI18NextTranslationFileView(APIView):
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (CanCreateI18NextTranslationFile, )

    def post(self, request: Request) -> Response:
        """
        Create an I18Next translation file from the JSON data.

        Args:
            request (Request): The incoming request containing JSON data.

        Returns:
            Response: A success response with the created JSON data.
        """
        # Generate filename
        translation_filename = 'i18next/translations.json'

        # Create ContentFile from JSON data and save to storage
        latest_file_content = json.dumps(request.data)

        # Ensure new_content is already in bytes format (if not, you can encode it)
        if not isinstance(latest_file_content, bytes):
            latest_file_content = latest_file_content.encode('utf-8')

        if default_storage.exists(translation_filename):
            # Overwrite the JSON data to storage
            with default_storage.open(translation_filename, 'wb') as translation_file:
                translation_file.write(latest_file_content)
        else:
            # Save JSON data to storage
            default_storage.save(translation_filename, ContentFile(latest_file_content))

        return Response(data=request.data, status=HTTP_201_CREATED)


class PublicRetrieveI18NextTranslationFileView(APIView):
    def get(self, request: Request, *args: set, **kwargs: dict) -> Response | FileResponse:
        """
        Retrieve the latest I18Next translation file.

        Args:
            request (Request): The incoming request.
            *args (set): Additional positional arguments.
            **kwargs (dict): Additional keyword arguments.

        Returns:
            Response | FileResponse: A FileResponse with the file content or Response (404) if the file doesn't exist.
        """
        # Build the file path within the storage
        file_path = 'i18next/translations.json'

        # Check if the file exists in storage
        if not default_storage.exists(file_path):
            return Response('Translation file not found.', status=HTTP_404_NOT_FOUND)

        # Determine the file's content type
        content_type, _ = mimetypes.guess_type(file_path)
        response = FileResponse(default_storage.open(file_path), content_type=content_type)
        return response
