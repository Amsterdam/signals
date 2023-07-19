# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.contrib.auth.models import Permission
from django.db.models import signals
from factory.django import mute_signals

from signals.apps.signals.factories import CategoryFactory
from signals.apps.signals.factories.status_message import (
    StatusMessageCategoryFactory,
    StatusMessageFactory
)
from signals.apps.signals.models import StatusMessage, StatusMessageCategory
from signals.test.utils import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestStatusMessageEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    TITLE = 'title'
    TEXT = 'text'
    STATE = 'o'
    ACTIVE = True
    PATH = '/signals/v1/private/status-messages/'

    def setUp(self):
        signals.post_save.disconnect(sender=StatusMessage, dispatch_uid='status_message_post_save_receiver')
        signals.post_delete.disconnect(sender=StatusMessage, dispatch_uid='status_message_post_delete_receiver')

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

    def test_categories_are_not_ignored_in_create(self):
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
        self.assertCountEqual([4, 5, 6], body['categories'])
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

    def test_categories_not_are_ignored_in_put(self):
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
        self.assertCountEqual([4, 5, 6], body['categories'])
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

    def test_categories_not_are_ignored_in_patch(self):
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
        self.assertCountEqual([4, 5, 6], body['categories'])
        self.assertIn('updated_at', body)
        self.assertIsNotNone(body['updated_at'])
        self.assertIn('created_at', body)
        self.assertIsNotNone(body['created_at'])

    def test_get_view_list(self):
        # In the setup of the test one status_message has already been created
        StatusMessageFactory.create_batch(4)

        response = self.client.get(self.PATH, format='json')
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body['count'], 5)
        self.assertEqual(len(body['results']), 5)

    def test_get_filter_list(self):
        # 1 status message for state 'm'
        StatusMessageFactory.create(state='m')

        # 2 status messages for state 'b'
        StatusMessageFactory.create_batch(2, state='b')

        # 3 status messages for state 'o' (In the setup of the test one status_message has already been created)
        StatusMessageFactory.create_batch(2, state='o')

        # 4 inactive random status messages
        StatusMessageFactory.create_batch(4, active=False)

        response = self.client.get(self.PATH, {'state': 'm'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'],
                         StatusMessage.objects.filter(state='m').count())

        response = self.client.get(self.PATH, {'state': 'b'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'],
                         StatusMessage.objects.filter(state='b').count())

        response = self.client.get(self.PATH, {'state': 'o'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'],
                         StatusMessage.objects.filter(state='o').count())

        response = self.client.get(self.PATH, {'state': ['m', 'b', ]}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'],
                         StatusMessage.objects.filter(state__in=['m', 'b', ]).count())

        response = self.client.get(self.PATH, {'active': False}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'],
                         StatusMessage.objects.filter(active=False).count())

        response = self.client.get(self.PATH, {'state': ['o', 'b', ], 'active': True}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'],
                         StatusMessage.objects.filter(state__in=['o', 'b', ], active=True).count())

    def test_update_categories_in_patch(self):
        response = self.client.patch(
            self.PATH + str(self.status_message.pk),
            {'categories': [4, 5, 6]},
            format='json'
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertIn('categories', body)
        self.assertCountEqual([4, 5, 6], body['categories'])

        response = self.client.patch(
            self.PATH + str(self.status_message.pk),
            {'categories': [4, 6, 8]},
            format='json'
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertIn('categories', body)
        self.assertCountEqual([4, 6, 8], body['categories'])

        response = self.client.patch(
            self.PATH + str(self.status_message.pk),
            {'categories': [9]},
            format='json'
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertIn('categories', body)
        self.assertCountEqual([9], body['categories'])


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

    def test_cannot_list_without_permission(self):
        response = self.client.get(self.PATH, format='json')
        self.assertEqual(403, response.status_code)


@mute_signals('post_save', 'post_delete')
class TestStatusMessageCategoryEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    PATH = '/signals/v1/private/status-messages/category'

    def setUp(self):
        statusmessagetemplate_write_permission = Permission.objects.get(
            codename='sia_statusmessage_write'
        )
        self.sia_read_write_user.user_permissions.add(statusmessagetemplate_write_permission)
        self.sia_read_write_user.save()

        self.client.force_authenticate(user=self.sia_read_write_user)

        self.category = CategoryFactory.create()

        self.status_messages = StatusMessageFactory.create_batch(5)

        for position in range(len(self.status_messages)):
            StatusMessageCategoryFactory.create(status_message=self.status_message,
                                                category=self.category,
                                                position=position)

    def test_post_new_positions(self):
        payload = [
            {
                'status_message': self.status_messages[1].pk,
                'position': 1,
            },
            {
                'status_message': self.status_messages[0].pk,
                'position': 2,
            },
            {
                'status_message': self.status_messages[2].pk,
                'position': 3,
            },
            {
                'status_message': self.status_messages[4].pk,
                'position': 4,
            },
            {
                'status_message': self.status_messages[3].pk,
                'position': 5,
            }
        ]

        response = self.client.post(f'{self.PATH}/{self.category.pk}/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), payload)

        for item in payload:
            status_message_from_db = StatusMessageCategory.objects.get(id=item['status_message'])
            self.assertEqual(status_message_from_db.position, item['position'])

    def test_post_new_position_single_item(self):
        payload = {
            'status_message': self.status_messages[1].pk,
            'position': 1,
        }

        response = self.client.post(f'{self.PATH}/{self.category.pk}/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), payload)

        status_message_from_db = StatusMessageCategory.objects.get(id=payload['status_message'])
        self.assertEqual(status_message_from_db.position, payload['position'])

    def test_post_duplicate_positions(self):
        payload = [
            {
                'status_message': self.status_messages[0].pk,
                'position': 1,
            },
            {
                'status_message': self.status_messages[1].pk,
                'position': 1,
            }
        ]

        response = self.client.post(f'{self.PATH}/{self.category.pk}/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertKeysEqual(response.json(), ['position'])
        self.assertEqual(response.json()['position'][0], 'Duplicate positions in request.')

    def test_post_duplicate_status_messages(self):
        payload = [
            {
                'status_message': self.status_messages[0].pk,
                'position': 1,
            },
            {
                'status_message': self.status_messages[0].pk,
                'position': 2,
            }
        ]

        response = self.client.post(f'{self.PATH}/{self.category.pk}/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertKeysEqual(response.json(), ['status_message'])
        self.assertEqual(response.json()['status_message'][0], 'Duplicate status messages in request.')

    def test_post_invalid_category(self):
        payload = [{'status_message': self.status_message[0].pk, 'position': 1}]

        response = self.client.post(f'{self.PATH}/1234567890/', payload, format='json')

        self.asserEqual(response.status_code, 400)
        self.assertKeysEqual(response.json(), ['category'])
        self.assertEqual(response.json()['category'][0], 'Category with id 1234567890 does not exist.')

        payload = {'status_message': self.status_message[0].pk, 'position': 1}

        response = self.client.post(f'{self.PATH}/1234567890/', payload, format='json')

        self.asserEqual(response.status_code, 400)
        self.assertKeysEqual(response.json(), ['category'])
        self.assertEqual(response.json()['category'][0], 'Category with id 1234567890 does not exist.')

    def test_post_invalid_status_message(self):
        payload = [{'status_message': 1234567890, 'position': 1}]

        response = self.client.post(f'{self.PATH}/{self.category.pk}/', payload, format='json')

        self.asserEqual(response.status_code, 400)
        self.assertKeysEqual(response.json()[0], ['status_message'])
        self.assertEqual(response.json()[0]['status_message'][0], 'Status message with id 1234567890 does not exist.')

        payload = {'status_message': 1234567890, 'position': 1}

        response = self.client.post(f'{self.PATH}/{self.category.pk}/', payload, format='json')

        self.asserEqual(response.status_code, 400)
        self.assertKeysEqual(response.json()[0], ['status_message'])
        self.assertEqual(response.json()[0]['status_message'][0], 'Status message with id 1234567890 does not exist.')
