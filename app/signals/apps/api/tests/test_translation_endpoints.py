# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import json
from typing import Any

from django.contrib.auth.models import Permission, User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.test import APITestCase

from signals.apps.api.views.translations import I18NEXT_TRANSLATION_FILE_PATH

TEST_TRANSLATION_DATA: dict[str, Any] = {
    "en": {
        "common": {
            "welcome": "Welcome to our website!",
            "language": "Language",
            "english": "English",
            "dutch": "Dutch",
        },
        "errors": {
            "notFound": "Page not found",
            "serverError": "Server error occurred"
        },
    },
    "nl": {
        "common": {
            "welcome": "Welkom op onze website!",
            "language": "Taal",
            "english": "Engels",
            "dutch": "nederlands",
        },
        "errors": {
            "notFound": "Pagina niet gevonden",
            "serverError": "Er is een serverfout opgetreden"
        },
    },
}


class PrivateCreateI18NextTranslationFileView(APITestCase):
    endpoint = '/signals/v1/private/translations/'

    def setUp(self) -> None:
        # Create a user with the necessary permission
        self.add_i18next_translation_file_permission: Permission = Permission.objects.get(
            codename='sia_add_i18next_translation_file'
        )
        self.user: User = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.user.user_permissions.add(
            self.add_i18next_translation_file_permission
        )

        self.client.force_authenticate(user=self.user)

    def tearDown(self) -> None:
        self.client.logout()

    def test_post_translation_new_file(self) -> None:
        """
        Posting a translation file with permission.

            1. Check that no file called "i18next/translations.js"
               exists initially
            2. Post the JSON blob to the specified URL
            3. Check that a file has been created in storage
               at "i18next/translations.js"
            4. Check that the contents of the file match the posted JSON blob
        """
        with self.settings(MEDIA_ROOT='/tmp/test_post_translation_new_file/'):

            # Check that no file called "i18next/translations.js"
            # exists initially
            self.assertFalse(
                default_storage.exists(I18NEXT_TRANSLATION_FILE_PATH)
            )

            # Post the JSON blob
            response = self.client.post(
                self.endpoint,
                data=json.dumps(TEST_TRANSLATION_DATA),
                content_type="application/json"
            )

            # Check that a file has been created
            self.assertEqual(response.status_code, 201)
            self.assertTrue(
                default_storage.exists(I18NEXT_TRANSLATION_FILE_PATH)
            )

            # Check that the contents of the file match the posted JSON blob
            with default_storage.open(I18NEXT_TRANSLATION_FILE_PATH) as file:
                file_contents: str = file.read().decode()
                self.assertEqual(
                    json.loads(file_contents),
                    TEST_TRANSLATION_DATA
                )

    def test_post_translation_file_already_exists(self) -> None:
        """
        Posting a translation file with an existing file.

            1. Create an existing translation file
            2. Post the JSON blob to the specified URL
            3. Check that a file still exists at "i18next/translations.js"
            4. Check that the contents of the file match the posted JSON blob
            5. Check that the contents of the file is no longer the same
               as before
        """
        with self.settings(MEDIA_ROOT='/tmp/test_post_translation_file_already_exists/'):

            # Create an existing translation file
            default_storage.save(
                I18NEXT_TRANSLATION_FILE_PATH,
                ContentFile("Existing file content")
            )

            # Post the JSON blob
            response = self.client.post(
                self.endpoint,
                data=json.dumps(TEST_TRANSLATION_DATA),
                content_type="application/json"
            )

            # Check that a file still exists
            self.assertEqual(response.status_code, 201)
            self.assertTrue(
                default_storage.exists(I18NEXT_TRANSLATION_FILE_PATH)
            )

            # Check that the contents of the file match the posted JSON blob
            with default_storage.open(I18NEXT_TRANSLATION_FILE_PATH) as file:
                file_contents: str = file.read().decode()
                self.assertEqual(
                    json.loads(file_contents),
                    TEST_TRANSLATION_DATA
                )

                # Check that the contents of the file are no longer the
                # same as before
                self.assertNotEqual(
                    file_contents,
                    "Existing file content"
                )

    def test_post_no_user_logged_in(self) -> None:
        """
        Posting without a logged-in user.

            1. Log the user out
            2. Post the JSON blob to the specified URL
            3. Check that the request is not allowed because the user is
               not logged in (HTTP 401 Unauthorized)
        """
        with self.settings(MEDIA_ROOT='/tmp/test_post_no_user_logged_in/'):

            # Log the user out
            self.client.logout()

            # Post the JSON blob
            response = self.client.post(
                self.endpoint,
                data=json.dumps(TEST_TRANSLATION_DATA),
                content_type="application/json"
            )

            # Check that the request is not allowed because the user is
            # not logged in
            self.assertEqual(response.status_code, 401)

    def test_post_no_permission(self) -> None:
        """
        Posting without the required permission.

            1. Remove the "add_i18next_translation_file" permission from
               the user
            2. Post the JSON blob to the specified URL
            3. Check that the request is not allowed because the user doesn't
               have the required permission (HTTP 403 Forbidden)
        """
        with self.settings(MEDIA_ROOT='/tmp/test_post_no_permission/'):

            # Remove the permission from the user
            self.user.user_permissions.remove(
                self.add_i18next_translation_file_permission
            )

            # Post the JSON blob
            response = self.client.post(
                self.endpoint,
                data=json.dumps(TEST_TRANSLATION_DATA),
                content_type="application/json"
            )

            # Check that the request is not allowed because the user doesn't
            # have the required permission
            self.assertEqual(response.status_code, 403)


class TestPublicRetrieveI18NextTranslationFileView(APITestCase):
    endpoint = '/signals/v1/public/translations.json'

    def test_retrieve_translation_file(self) -> None:
        """
        Retrieving the translation file

            1. Generate test file
            3. Retrieve the contents of the translation file
            4. Check that the retrieved contents match the posted JSON blob
        """
        with self.settings(MEDIA_ROOT='/tmp/test_retrieve_translation_file/'):

            # Create an existing translation file
            default_storage.save(
                I18NEXT_TRANSLATION_FILE_PATH,
                ContentFile(json.dumps(TEST_TRANSLATION_DATA))
            )

            # Retrieve the contents of the file
            response_retrieve = self.client.get(self.endpoint)

            self.assertEqual(response_retrieve.status_code, 200)

            # Check that the retrieved content matches the posted JSON blob
            file_contents = response_retrieve.streaming_content
            content_file = ContentFile(b"".join(file_contents))

            self.assertEqual(
                json.loads(content_file.read().decode()),
                TEST_TRANSLATION_DATA
            )

    def test_retrieve_file_does_no_exist(self) -> None:
        """
        Retrieving the translation file does not exist.

            1. Attempt to retrieve a file that does not exist
            2. Check that a 404 response is raised (HTTP 404 Not Found)
        """
        with self.settings(MEDIA_ROOT='/tmp/test_retrieve_file_does_no_exist/'):

            # Delete the translation file if it already exists
            if default_storage.exists(I18NEXT_TRANSLATION_FILE_PATH):
                default_storage.delete(I18NEXT_TRANSLATION_FILE_PATH)

            # Attempt to retrieve a nonexistent file
            response = self.client.get(self.endpoint)

            # Check that a 404 response is raised
            self.assertEqual(response.status_code, 404)
