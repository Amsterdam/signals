# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.contrib.auth.models import Permission

from signals.apps.signals.factories import CategoryFactory
from signals.apps.signals.factories.status_message import (
    StatusMessageCategoryFactory,
    StatusMessageFactory
)
from signals.apps.signals.models import StatusMessageCategory
from signals.test.utils import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestStatusMessageEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    TITLE = 'title'
    TEXT = 'text'
    STATE = 'o'
    ACTIVE = True
    PATH = '/signals/v1/private/status-messages/'

    def setUp(self):
        statusmessagetemplate_write_permission = Permission.objects.get(
            codename='sia_statusmessage_write'
        )
        self.sia_read_write_user.user_permissions.add(statusmessagetemplate_write_permission)
        self.sia_read_write_user.save()
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.status_message = StatusMessageFactory.create(
            title=self.TITLE,
            text=self.TEXT,
            state=self.STATE,
            active=self.ACTIVE
        )

    # Basic tests
    def test_can_create(self):
        response = self.client.post(
            self.PATH,
            {'title': self.TITLE, 'text': self.TEXT, 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 201)

        body = response.json()
        self.assertIn('id', body)
        self.assertEqual(2, body['id'])
        self.assertIn('title', body)
        self.assertEqual(self.TITLE, body['title'])
        self.assertIn('text', body)
        self.assertEqual(self.TEXT, body['text'])
        self.assertIn('active', body)
        self.assertEqual(self.ACTIVE, body['active'])
        self.assertIn('state', body)
        self.assertEqual(self.STATE, body['state'])
        self.assertIn('categories', body)
        self.assertListEqual([], body['categories'])
        self.assertIn('updated_at', body)
        self.assertIsNotNone(body['updated_at'])
        self.assertIn('created_at', body)
        self.assertIsNotNone(body['created_at'])

    def test_can_read(self):
        response = self.client.get(self.PATH + str(self.status_message.pk))

        self.assertEqual(200, response.status_code)

        body = response.json()
        self.assertIn('id', body)
        self.assertEqual(self.status_message.pk, body['id'])
        self.assertIn('title', body)
        self.assertEqual(self.TITLE, body['title'])
        self.assertIn('text', body)
        self.assertEqual(self.TEXT, body['text'])
        self.assertIn('active', body)
        self.assertEqual(self.ACTIVE, body['active'])
        self.assertIn('state', body)
        self.assertEqual(self.STATE, body['state'])
        self.assertIn('categories', body)
        self.assertListEqual([], body['categories'])
        self.assertIn('updated_at', body)
        self.assertIsNotNone(body['updated_at'])
        self.assertIn('created_at', body)
        self.assertIsNotNone(body['created_at'])

    def test_can_put(self):
        id = self.status_message.pk
        title = 'new title'
        text = 'new text'
        active = False
        state = 'm'

        response = self.client.put(
            self.PATH + str(id),
            {'title': title, 'text': text, 'active': active, 'state': state},
            format='json'
        )

        self.assertEqual(200, response.status_code)

        body = response.json()
        self.assertIn('id', body)
        self.assertEqual(id, body['id'])
        self.assertIn('title', body)
        self.assertEqual(title, body['title'])
        self.assertIn('text', body)
        self.assertEqual(text, body['text'])
        self.assertIn('active', body)
        self.assertEqual(active, body['active'])
        self.assertIn('state', body)
        self.assertEqual(state, body['state'])
        self.assertIn('categories', body)
        self.assertListEqual([], body['categories'])
        self.assertIn('updated_at', body)
        self.assertIsNotNone(body['updated_at'])
        self.assertIn('created_at', body)
        self.assertIsNotNone(body['created_at'])

    def test_can_patch_title(self):
        id = self.status_message.pk
        title = 'patched title'

        response = self.client.patch(
            self.PATH + str(id),
            {'title': title},
            format='json'
        )

        self.assertEqual(200, response.status_code)

        body = response.json()
        self.assertIn('id', body)
        self.assertEqual(id, body['id'])
        self.assertIn('title', body)
        self.assertEqual(title, body['title'])
        self.assertIn('text', body)
        self.assertEqual(self.TEXT, body['text'])
        self.assertIn('active', body)
        self.assertEqual(self.ACTIVE, body['active'])
        self.assertIn('state', body)
        self.assertEqual(self.STATE, body['state'])
        self.assertIn('categories', body)
        self.assertListEqual([], body['categories'])
        self.assertIn('updated_at', body)
        self.assertIsNotNone(body['updated_at'])
        self.assertIn('created_at', body)
        self.assertIsNotNone(body['created_at'])

    def test_can_patch_text(self):
        id = self.status_message.pk
        text = 'patched text'

        response = self.client.patch(
            self.PATH + str(id),
            {'text': text},
            format='json'
        )

        self.assertEqual(200, response.status_code)

        body = response.json()
        self.assertIn('id', body)
        self.assertEqual(id, body['id'])
        self.assertIn('title', body)
        self.assertEqual(self.TITLE, body['title'])
        self.assertIn('text', body)
        self.assertEqual(text, body['text'])
        self.assertIn('active', body)
        self.assertEqual(self.ACTIVE, body['active'])
        self.assertIn('state', body)
        self.assertEqual(self.STATE, body['state'])
        self.assertIn('categories', body)
        self.assertListEqual([], body['categories'])
        self.assertIn('updated_at', body)
        self.assertIsNotNone(body['updated_at'])
        self.assertIn('created_at', body)
        self.assertIsNotNone(body['created_at'])

    def test_can_patch_active(self):
        id = self.status_message.pk
        active = False

        response = self.client.patch(
            self.PATH + str(id),
            {'active': active},
            format='json'
        )

        self.assertEqual(200, response.status_code)

        body = response.json()
        self.assertIn('id', body)
        self.assertEqual(id, body['id'])
        self.assertIn('title', body)
        self.assertEqual(self.TITLE, body['title'])
        self.assertIn('text', body)
        self.assertEqual(self.TEXT, body['text'])
        self.assertIn('active', body)
        self.assertEqual(active, body['active'])
        self.assertIn('state', body)
        self.assertEqual(self.STATE, body['state'])
        self.assertIn('categories', body)
        self.assertListEqual([], body['categories'])
        self.assertIn('updated_at', body)
        self.assertIsNotNone(body['updated_at'])
        self.assertIn('created_at', body)
        self.assertIsNotNone(body['created_at'])

    def test_can_patch_state(self):
        id = self.status_message.pk
        state = 'm'

        response = self.client.patch(
            self.PATH + str(id),
            {'state': state},
            format='json'
        )

        self.assertEqual(200, response.status_code)

        body = response.json()
        self.assertIn('id', body)
        self.assertEqual(id, body['id'])
        self.assertIn('title', body)
        self.assertEqual(self.TITLE, body['title'])
        self.assertIn('text', body)
        self.assertEqual(self.TEXT, body['text'])
        self.assertIn('active', body)
        self.assertEqual(self.ACTIVE, body['active'])
        self.assertIn('state', body)
        self.assertEqual(state, body['state'])
        self.assertIn('categories', body)
        self.assertListEqual([], body['categories'])
        self.assertIn('updated_at', body)
        self.assertIsNotNone(body['updated_at'])
        self.assertIn('created_at', body)
        self.assertIsNotNone(body['created_at'])

    def test_can_delete(self):
        response = self.client.delete(self.PATH + str(self.status_message.pk))

        self.assertEqual(204, response.status_code)

    def test_can_delete_when_attached_to_categories(self):
        category = CategoryFactory.create()
        StatusMessageCategoryFactory.create(status_message=self.status_message, category=category, position=1)

        response = self.client.delete(self.PATH + str(self.status_message.pk))

        self.assertEqual(204, response.status_code)
        self.assertEqual(0, StatusMessageCategory.objects.count())

    # Validation tests
    def test_cannot_create_without_title(self):
        response = self.client.post(
            self.PATH,
            {'text': self.TEXT, 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('title', body)
        self.assertListEqual(['Dit veld is vereist.'], body['title'])

    def test_cannot_create_with_blank_title(self):
        response = self.client.post(
            self.PATH,
            {'title': '', 'text': self.TEXT, 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('title', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['title'])

    def test_cannot_create_with_null_title(self):
        response = self.client.post(
            self.PATH,
            {'title': None, 'text': self.TEXT, 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('title', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['title'])

    def test_cannot_create_without_text(self):
        response = self.client.post(
            self.PATH,
            {'title': self.TITLE, 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('text', body)
        self.assertListEqual(['Dit veld is vereist.'], body['text'])

    def test_cannot_create_with_blank_text(self):
        response = self.client.post(
            self.PATH,
            {'title': self.TITLE, 'text': '', 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('text', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['text'])

    def test_cannot_create_with_null_text(self):
        response = self.client.post(
            self.PATH,
            {'title': self.TITLE, 'text': None, 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('text', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['text'])

    def test_can_create_without_active(self):
        response = self.client.post(
            self.PATH,
            {'title': self.TITLE, 'text': self.TEXT, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 201)

        body = response.json()
        self.assertIn('active', body)
        self.assertFalse(body['active'])

    def test_cannot_create_without_state(self):
        response = self.client.post(
            self.PATH,
            {'title': self.TITLE, 'text': self.TEXT, 'active': self.ACTIVE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('state', body)
        self.assertListEqual(['Dit veld is vereist.'], body['state'])

    def test_cannot_create_with_blank_state(self):
        response = self.client.post(
            self.PATH,
            {'title': self.TITLE, 'text': self.TEXT, 'active': self.ACTIVE, 'state': ''},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('state', body)
        self.assertListEqual(['"" is een ongeldige keuze.'], body['state'])

    def test_cannot_create_with_non_existing_state(self):
        response = self.client.post(
            self.PATH,
            {'title': self.TITLE, 'text': self.TEXT, 'active': self.ACTIVE, 'state': 'bla'},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('state', body)
        self.assertListEqual(['"bla" is een ongeldige keuze.'], body['state'])

    def test_cannot_create_with_null_state(self):
        response = self.client.post(
            self.PATH,
            {'title': self.TITLE, 'text': self.TEXT, 'active': self.ACTIVE, 'state': None},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('state', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['state'])

    def test_categories_are_ignored_in_create(self):
        response = self.client.post(
            self.PATH,
            {
                'title': self.TITLE,
                'text': self.TEXT,
                'active': self.ACTIVE,
                'state': self.STATE,
                'categories': [4, 5, 6]
            },
            format='json'
        )

        self.assertEqual(response.status_code, 201)

        body = response.json()
        self.assertIn('id', body)
        self.assertNotEqual(self.status_message.pk, body['id'])
        self.assertIn('title', body)
        self.assertEqual(self.TITLE, body['title'])
        self.assertIn('text', body)
        self.assertEqual(self.TEXT, body['text'])
        self.assertIn('active', body)
        self.assertEqual(self.ACTIVE, body['active'])
        self.assertIn('state', body)
        self.assertEqual(self.STATE, body['state'])
        self.assertIn('categories', body)
        self.assertListEqual([], body['categories'])
        self.assertIn('updated_at', body)
        self.assertIsNotNone(body['updated_at'])
        self.assertIn('created_at', body)
        self.assertIsNotNone(body['created_at'])

    def test_cannot_put_without_title(self):
        response = self.client.put(
            self.PATH + str(self.status_message.pk),
            {'text': self.TEXT, 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('title', body)
        self.assertListEqual(['Dit veld is vereist.'], body['title'])

    def test_cannot_put_with_blank_title(self):
        response = self.client.put(
            self.PATH + str(self.status_message.pk),
            {'title': '', 'text': self.TEXT, 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('title', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['title'])

    def test_cannot_put_with_null_title(self):
        response = self.client.put(
            self.PATH + str(self.status_message.pk),
            {'title': None, 'text': self.TEXT, 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('title', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['title'])

    def test_cannot_put_without_text(self):
        response = self.client.put(
            self.PATH + str(self.status_message.pk),
            {'title': self.TITLE, 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('text', body)
        self.assertListEqual(['Dit veld is vereist.'], body['text'])

    def test_cannot_put_with_blank_text(self):
        response = self.client.put(
            self.PATH + str(self.status_message.pk),
            {'title': self.TITLE, 'text': '', 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('text', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['text'])

    def test_cannot_put_with_null_text(self):
        response = self.client.put(
            self.PATH + str(self.status_message.pk),
            {'title': self.TITLE, 'text': None, 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('text', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['text'])

    def test_can_put_without_active(self):
        title = 'put title'
        text = 'put text'
        state = 'm'

        response = self.client.put(
            self.PATH + str(self.status_message.pk),
            {'title': title, 'text': text, 'state': state},
            format='json'
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertIn('active', body)
        self.assertTrue(body['active'])
        self.assertIn('title', body)
        self.assertEqual(title, body['title'])
        self.assertIn('text', body)
        self.assertEqual(text, body['text'])
        self.assertIn('state', body)
        self.assertEqual(state, body['state'])

    def test_cannot_put_without_state(self):
        response = self.client.put(
            self.PATH + str(self.status_message.pk),
            {'title': self.TITLE, 'text': self.TEXT, 'active': self.ACTIVE},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('state', body)
        self.assertListEqual(['Dit veld is vereist.'], body['state'])

    def test_cannot_put_with_blank_state(self):
        response = self.client.put(
            self.PATH + str(self.status_message.pk),
            {'title': self.TITLE, 'text': self.TEXT, 'active': self.ACTIVE, 'state': ''},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('state', body)
        self.assertListEqual(['"" is een ongeldige keuze.'], body['state'])

    def test_cannot_put_with_non_existing_state(self):
        response = self.client.put(
            self.PATH + str(self.status_message.pk),
            {'title': self.TITLE, 'text': self.TEXT, 'active': self.ACTIVE, 'state': 'bla'},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('state', body)
        self.assertListEqual(['"bla" is een ongeldige keuze.'], body['state'])

    def test_cannot_put_with_null_state(self):
        response = self.client.put(
            self.PATH + str(self.status_message.pk),
            {'title': self.TITLE, 'text': self.TEXT, 'active': self.ACTIVE, 'state': None},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('state', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['state'])

    def test_categories_are_ignored_in_put(self):
        title = 'put title'
        text = 'put text'
        active = False
        state = 'm'

        response = self.client.put(
            self.PATH + str(self.status_message.pk),
            {
                'title': title,
                'text': text,
                'active': active,
                'state': state,
                'categories': [4, 5, 6]
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertIn('id', body)
        self.assertEqual(self.status_message.pk, body['id'])
        self.assertIn('title', body)
        self.assertEqual(title, body['title'])
        self.assertIn('text', body)
        self.assertEqual(text, body['text'])
        self.assertIn('active', body)
        self.assertEqual(active, body['active'])
        self.assertIn('state', body)
        self.assertEqual(state, body['state'])
        self.assertIn('categories', body)
        self.assertListEqual([], body['categories'])
        self.assertIn('updated_at', body)
        self.assertIsNotNone(body['updated_at'])
        self.assertIn('created_at', body)
        self.assertIsNotNone(body['created_at'])

    def test_cannot_patch_with_blank_title(self):
        response = self.client.patch(
            self.PATH + str(self.status_message.pk),
            {'title': ''},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('title', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['title'])

    def test_cannot_patch_with_null_title(self):
        response = self.client.patch(
            self.PATH + str(self.status_message.pk),
            {'title': None},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('title', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['title'])

    def test_cannot_patch_with_blank_text(self):
        response = self.client.patch(
            self.PATH + str(self.status_message.pk),
            {'text': ''},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('text', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['text'])

    def test_cannot_patch_with_null_text(self):
        response = self.client.patch(
            self.PATH + str(self.status_message.pk),
            {'text': None},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('text', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['text'])

    def test_cannot_patch_with_blank_state(self):
        response = self.client.patch(
            self.PATH + str(self.status_message.pk),
            {'state': ''},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('state', body)
        self.assertListEqual(['"" is een ongeldige keuze.'], body['state'])

    def test_cannot_patch_with_non_existing_state(self):
        response = self.client.patch(
            self.PATH + str(self.status_message.pk),
            {'state': 'bla'},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('state', body)
        self.assertListEqual(['"bla" is een ongeldige keuze.'], body['state'])

    def test_cannot_patch_with_null_state(self):
        response = self.client.patch(
            self.PATH + str(self.status_message.pk),
            {'state': None},
            format='json'
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        self.assertIn('state', body)
        self.assertListEqual(['Dit veld mag niet leeg zijn.'], body['state'])

    def test_categories_are_ignored_in_patch(self):
        response = self.client.patch(
            self.PATH + str(self.status_message.pk),
            {'categories': [4, 5, 6]},
            format='json'
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertIn('id', body)
        self.assertEqual(self.status_message.pk, body['id'])
        self.assertIn('title', body)
        self.assertEqual(self.TITLE, body['title'])
        self.assertIn('text', body)
        self.assertEqual(self.TEXT, body['text'])
        self.assertIn('active', body)
        self.assertEqual(self.ACTIVE, body['active'])
        self.assertIn('state', body)
        self.assertEqual(self.STATE, body['state'])
        self.assertIn('categories', body)
        self.assertListEqual([], body['categories'])
        self.assertIn('updated_at', body)
        self.assertIsNotNone(body['updated_at'])
        self.assertIn('created_at', body)
        self.assertIsNotNone(body['created_at'])


class TestStatusMessageEndpointPermissions(SignalsBaseApiTestCase):
    TITLE = 'title'
    TEXT = 'text'
    STATE = 'o'
    ACTIVE = True
    PATH = '/signals/v1/private/status-messages/'

    def setUp(self):
        self.client.force_authenticate(user=self.user)

        self.status_message = StatusMessageFactory.create(
            title=self.TITLE,
            text=self.TEXT,
            state=self.STATE,
            active=self.ACTIVE
        )

    # Permission tests
    def test_cannot_create_without_permission(self):
        response = self.client.post(
            self.PATH,
            {'title': self.TITLE, 'text': self.TEXT, 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(403, response.status_code)

    def test_cannot_read_without_permission(self):
        response = self.client.get(self.PATH + str(self.status_message.pk))

        self.assertEqual(403, response.status_code)

    def test_cannot_put_without_permission(self):
        response = self.client.put(
            self.PATH + str(self.status_message.pk),
            {'title': self.TITLE, 'text': self.TEXT, 'active': self.ACTIVE, 'state': self.STATE},
            format='json'
        )

        self.assertEqual(403, response.status_code)

    def test_cannot_patch_without_permission(self):
        response = self.client.patch(
            self.PATH + str(self.status_message.pk),
            {'title': 'patch title'},
            format='json'
        )

        self.assertEqual(403, response.status_code)

    def test_cannot_delete_without_permission(self):
        response = self.client.delete(self.PATH + str(self.status_message.pk))

        self.assertEqual(403, response.status_code)
