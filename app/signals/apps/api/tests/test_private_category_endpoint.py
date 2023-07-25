# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
import os

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from signals.apps.signals.factories import CategoryFactory, ParentCategoryFactory
from signals.apps.signals.factories.category import CategoryWithIconFactory
from signals.apps.signals.models import CategoryDepartment
from signals.test.utils import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestPrivateCategoryEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        sia_category_write_permission = Permission.objects.get(codename='sia_category_write')
        self.sia_read_write_user.user_permissions.add(sia_category_write_permission)

        self.parent_category = ParentCategoryFactory.create()

        CategoryFactory.create_batch(5, parent=self.parent_category)
        self.parent_category.refresh_from_db()

        super().setUp()

    def _assert_category_data(self, category, data):
        private_url = f'http://testserver/signals/v1/private/categories/{category.pk}'
        if category.is_parent():
            public_url = f'http://testserver/signals/v1/public/terms/categories/{category.slug}'
            status_message_templates_url = f'http://testserver/signals/v1/private/terms/categories/{category.slug}/status-message-templates'  # noqa
        else:
            public_url = f'http://testserver/signals/v1/public/terms/categories/{category.parent.slug}/sub_categories/{category.slug}'  # noqa
            status_message_templates_url = f'http://testserver/signals/v1/private/terms/categories/{category.parent.slug}/sub_categories/{category.slug}/status-message-templates'  # noqa

        self.assertIn('_links', data)

        links = data['_links']
        self.assertIn('curies', links)
        self.assertIn('name', links['curies'])
        self.assertEqual('sia', links['curies']['name'])
        self.assertIn('self', links)
        self.assertIn('href', links['self'])
        self.assertEqual(private_url, links['self']['href'])
        self.assertIn('public', links['self'])
        self.assertEqual(public_url, links['self']['public'])
        self.assertIn('sia:status-message-templates', links)
        self.assertEqual(status_message_templates_url, links['sia:status-message-templates']['href'])

        self.assertIn('_display', data)
        self.assertIn('id', data)
        self.assertEqual(category.pk, data['id'])
        self.assertIn('name', data)
        self.assertEqual(category.name, data['name'])
        self.assertIn('slug', data)
        self.assertEqual(category.slug, data['slug'])
        self.assertIn('is_active', data)
        self.assertEqual(data['is_active'], category.is_active)
        self.assertEqual(data['description'], category.description)
        self.assertEqual(data['handling_message'], category.handling_message)
        self.assertEqual(data['public_name'], category.public_name)
        self.assertEqual(data['is_public_accessible'], category.is_public_accessible)

        self.assertIn('sla', data)
        if category.slo.count() > 0:
            slo = category.slo.all().order_by('-created_at').first()
            self.assertEqual(data['sla']['n_days'], slo.n_days)
            self.assertEqual(data['sla']['use_calendar_days'], slo.use_calendar_days)

        self.assertIn('departments', data)
        if category.departments.count() > 0:
            self.assertEqual(category.departments.count(), len(data['departments']))
            category_departments = CategoryDepartment.objects.filter(
                category_id=category.pk
            ).order_by(
                'department__code'
            )
            for counter, category_department in enumerate(category_departments):
                # Check if the expected departments are present in the json output
                department_data = data['departments'][counter]

                self.assertEqual(department_data['id'], category_department.department.pk)
                self.assertEqual(department_data['code'], category_department.department.code)
                self.assertEqual(department_data['name'], category_department.department.name)
                self.assertEqual(str(department_data['is_intern']), str(category_department.department.is_intern))
                self.assertEqual(str(department_data['is_responsible']), str(category_department.is_responsible))
                self.assertEqual(str(department_data['can_view']), str(category_department.can_view))
        else:
            self.assertEqual(0, len(data['departments']))

        self.assertIn('note', data)
        self.assertEqual(data['note'], category.note)

    def test_list_categories(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = '/signals/v1/private/categories/?page_size=1000'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['count'], 174)
        self.assertEqual(len(data['results']), 174)

    def test_get_parent_category(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = f'/signals/v1/private/categories/{self.parent_category.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._assert_category_data(category=self.parent_category, data=response.json())

    def test_patch_parent_category(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = f'/signals/v1/private/categories/{self.parent_category.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._assert_category_data(category=self.parent_category, data=response.json())

        response = self.client.patch(url, data={'name': 'Patched name', 'is_active': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.parent_category.refresh_from_db()
        self._assert_category_data(category=self.parent_category, data=response.json())

    def test_get_child_category(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        category = self.parent_category.children.first()

        url = f'/signals/v1/private/categories/{category.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._assert_category_data(category=category, data=response.json())

    def test_patch_child_category(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        category = self.parent_category.children.first()

        url = f'/signals/v1/private/categories/{category.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._assert_category_data(category=category, data=response.json())

        data = {
            'name': 'Patched name',
            'description': 'Patched description',
            'new_sla': {
                'n_days': 5,
                'use_calendar_days': True
            },
            'handling_message': 'Patched handling message',
            'note': 'Very important note!',
        }

        response = self.client.patch(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        category.refresh_from_db()
        self._assert_category_data(category=category, data=response.json())

    def test_post_category(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = '/signals/v1/private/categories/'
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_category(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = f'/signals/v1/private/categories/{self.parent_category.pk}'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_not_logged_in(self):
        url = '/signals/v1/private/categories/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        url = f'/signals/v1/private/categories/{self.parent_category.pk}'

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.patch(url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_history_view(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = f'/signals/v1/private/categories/{self.parent_category.pk}'

        response = self.client.patch(url, data={'note': 'This is a note'})  # must not show up in category history
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.patch(url, data={'name': 'Patched name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.patch(url, data={'name': 'Patched name again', 'is_active': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        history_url = f'{url}/history'
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(len(response_data), 2)

        change_log_data = response_data[0]
        self.assertEqual(change_log_data['what'], 'UPDATED_CATEGORY')
        self.assertIsNone(change_log_data['description'])
        self.assertEqual(change_log_data['who'], self.sia_read_write_user.username)
        self.assertIn('Naam gewijzigd naar:\n Patched name again', change_log_data['action'])
        self.assertIn('Status gewijzigd naar:\n Inactief', change_log_data['action'])

        change_log_data = response_data[1]
        self.assertEqual(change_log_data['what'], 'UPDATED_CATEGORY')
        self.assertIsNone(change_log_data['description'])
        self.assertEqual(change_log_data['who'], self.sia_read_write_user.username)
        self.assertIn('Naam gewijzigd naar:\n Patched name', change_log_data['action'])

    def test_history_view_update_handling_message(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = f'/signals/v1/private/categories/{self.parent_category.pk}'

        response = self.client.patch(url, data={'handling_message': 'Patched handling message'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        history_url = f'{url}/history'
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(len(response_data), 1)

        change_log_data = response_data[0]
        self.assertEqual(change_log_data['what'], 'UPDATED_CATEGORY')
        self.assertIsNone(change_log_data['description'])
        self.assertEqual(change_log_data['who'], self.sia_read_write_user.username)
        self.assertIn('Servicebelofte gewijzigd naar:\n Patched handling message', change_log_data['action'])

    def test_patch_category_multiple_unchanged_slo_calls(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        category = self.parent_category.children.first()
        slo_count_at_start_of_tests = category.slo.count()

        url = f'/signals/v1/private/categories/{category.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._assert_category_data(category=category, data=response.json())

        # Add a SLO
        data = {'new_sla': {'n_days': 5, 'use_calendar_days': True}}
        response = self.client.patch(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        category.refresh_from_db()
        self.assertEqual(category.slo.count(), slo_count_at_start_of_tests + 1)
        self._assert_category_data(category=category, data=response.json())

        # Patch SLO 5 times without changing any data to the SLO
        for x in range(5):
            data = {'new_sla': {'n_days': 5, 'use_calendar_days': True}}
            response = self.client.patch(url, data=data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self._assert_category_data(category=category, data=response.json())

        category.refresh_from_db()
        self.assertEqual(category.slo.count(), slo_count_at_start_of_tests + 1)

    def test_patch_category_public_parameters(self):
        """
        Change the public_name and/or the is_public_accessible parameters of a Category
        """
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = f'/signals/v1/private/categories/{self.parent_category.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._assert_category_data(category=self.parent_category, data=response.json())

        response = self.client.patch(url, data={'public_name': 'Public name', 'is_public_accessible': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.parent_category.refresh_from_db()
        self._assert_category_data(category=self.parent_category, data=response.json())

        response = self.client.patch(url, data={'public_name': f'{self.parent_category.name} (Public name)'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.parent_category.refresh_from_db()
        self._assert_category_data(category=self.parent_category, data=response.json())

        response = self.client.patch(url, data={'is_public_accessible': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.parent_category.refresh_from_db()
        self._assert_category_data(category=self.parent_category, data=response.json())

    def test_history_public_parameters(self):
        # Changes to the public parameters should be logged in the history of a Category
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = f'/signals/v1/private/categories/{self.parent_category.pk}'

        # Test public_name changed in history

        response = self.client.patch(url, data={'public_name': f'{self.parent_category.name} (Public name)'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.parent_category.refresh_from_db()
        self._assert_category_data(category=self.parent_category, data=response.json())

        history_url = f'{url}/history'
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(len(response_data), 1)

        change_log_data = response_data[0]
        self.assertEqual(change_log_data['what'], 'UPDATED_CATEGORY')
        self.assertIsNone(change_log_data['description'])
        self.assertEqual(change_log_data['who'], self.sia_read_write_user.username)
        self.assertIn(f'Naam openbaar gewijzigd naar:\n {self.parent_category.name} (Public name)',
                      change_log_data['action'])

        # Test is_public_accessible set to True in history

        response = self.client.patch(url, data={'is_public_accessible': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.parent_category.refresh_from_db()
        self._assert_category_data(category=self.parent_category, data=response.json())

        response = self.client.get(history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(len(response_data), 2)

        change_log_data = response_data[0]
        self.assertEqual(change_log_data['what'], 'UPDATED_CATEGORY')
        self.assertIsNone(change_log_data['description'])
        self.assertEqual(change_log_data['who'], self.sia_read_write_user.username)
        self.assertIn('Openbaar tonen gewijzigd naar:\n Aan', change_log_data['action'])

        # Test is_public_accessible set to False in history

        response = self.client.patch(url, data={'is_public_accessible': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.parent_category.refresh_from_db()
        self._assert_category_data(category=self.parent_category, data=response.json())

        response = self.client.get(history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(len(response_data), 3)

        change_log_data = response_data[0]
        self.assertEqual(change_log_data['what'], 'UPDATED_CATEGORY')
        self.assertIsNone(change_log_data['description'])
        self.assertEqual(change_log_data['who'], self.sia_read_write_user.username)
        self.assertIn('Openbaar tonen gewijzigd naar:\n Uit', change_log_data['action'])

    def test_patch_configuration_parent_category(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        url = f'/signals/v1/private/categories/{self.parent_category.pk}'
        configuration = {'show_children_in_filter': True}

        response = self.client.patch(
            url,
            data={'configuration': configuration},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertIn('configuration', body)
        self.assertDictEqual(body['configuration'], configuration)

    def test_patch_configuration_parent_category_show_children_in_filter_missing(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        url = f'/signals/v1/private/categories/{self.parent_category.pk}'
        configuration = {'bla': 'diebla'}

        response = self.client.patch(
            url,
            data={'configuration': configuration},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        body = response.json()
        self.assertIn('configuration', body)
        self.assertIn('The "show_children_in_filter" is required for parent categories', body['configuration'])

    def test_patch_configuration_parent_category_show_children_in_filter_incorrect_value_type(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        url = f'/signals/v1/private/categories/{self.parent_category.pk}'
        configuration = {'show_children_in_filter': 'string'}

        response = self.client.patch(
            url,
            data={'configuration': configuration},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        body = response.json()
        self.assertIn('configuration', body)
        self.assertIn('Value of "show_children_in_filter" is not a valid boolean', body['configuration'])

    def test_patch_configuration_parent_category_extra_configuration_value(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        url = f'/signals/v1/private/categories/{self.parent_category.pk}'
        configuration = {
            'show_children_in_filter': False,
            'bla': 'diebla'
        }

        response = self.client.patch(
            url,
            data={'configuration': configuration},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        body = response.json()
        self.assertIn('configuration', body)
        self.assertIn('Only "show_children_in_filter" is allowed', body['configuration'])

    def test_patch_configuration_child_category(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        url = f'/signals/v1/private/categories/{self.parent_category.children.first().pk}'
        configuration = {'show_children_in_filter': False}

        response = self.client.patch(
            url,
            data={'configuration': configuration},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        body = response.json()
        self.assertIn('configuration', body)
        self.assertIn('No additional configuration allowed for child categories', body['configuration'])

    def test_get_detail_configuration_present(self):
        configuration = {'show_children_in_filter': False}
        self.parent_category.configuration = configuration
        self.parent_category.save()

        self.client.force_authenticate(user=self.sia_read_write_user)
        url = f'/signals/v1/private/categories/{self.parent_category.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertIn('configuration', body)
        self.assertDictEqual(body['configuration'], configuration)

    def test_get_list_configuration_present(self):
        configuration = {'show_children_in_filter': False}
        self.parent_category.configuration = configuration
        self.parent_category.save()

        self.client.force_authenticate(user=self.sia_read_write_user)
        url = '/signals/v1/private/categories/?page_size=1000'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()

        self.assertIn('results', body)
        parent = None
        for category in body['results']:
            print(category['id'], self.parent_category.pk)
            if category['id'] == self.parent_category.pk:
                parent = category

        self.assertIsNotNone(parent)
        self.assertIn('configuration', parent)
        self.assertDictEqual(parent['configuration'], configuration)


class TestPrivateCategoryIconEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        """
        Add the correct permission to the user.
        Create a parent category with no icon.
        Create a child category with an icon.
        Get the content of 2 test files (gif and png).
        """
        sia_category_write_permission = Permission.objects.get(codename='sia_category_write')
        self.sia_read_write_user.user_permissions.add(sia_category_write_permission)

        self.parent_category = ParentCategoryFactory.create()
        self.category = CategoryWithIconFactory.create(parent=self.parent_category)

        gif_filename = os.path.join(os.path.dirname(__file__), 'test-data', 'test.gif')
        with open(gif_filename, 'rb') as gif_file:
            self.gif_content = gif_file.read()

        jpg_filename = os.path.join(os.path.dirname(__file__), 'test-data', 'test.jpg')
        with open(jpg_filename, 'rb') as jpg_file:
            self.jpg_content = jpg_file.read()

    def test_add_update_icon(self):
        """
        The following 2 cases are tested:
         - Add an icon (category has no icon)
         - Replace an icon (category already has an icon)
        """
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.assertEqual(self.parent_category.icon, None)
        endpoint = f'/signals/v1/private/categories/{self.parent_category.pk}/icon'
        data = {'icon': SimpleUploadedFile('image.gif', self.gif_content, content_type='image/gif')}
        response = self.client.put(endpoint, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.parent_category.refresh_from_db()
        self.assertNotEqual(self.parent_category.icon, None)
        self.assertEqual(self.parent_category.icon.read(), self.gif_content)

        original_category_icon_name = self.category.icon.name
        self.assertIsNotNone(self.category.icon)
        endpoint = f'/signals/v1/private/categories/{self.category.pk}/icon'
        data = {'icon': SimpleUploadedFile('image.jpg', self.jpg_content, content_type='image/jpeg')}
        response = self.client.patch(endpoint, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.category.refresh_from_db()
        self.assertNotEqual(self.category.icon.name, original_category_icon_name)
        self.assertEqual(self.category.icon.read(), self.jpg_content)

    def test_add_update_icon_required(self):
        """
        The icon is required when adding/updating
        """
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.assertEqual(self.parent_category.icon, None)
        endpoint = f'/signals/v1/private/categories/{self.parent_category.pk}/icon'
        data = {}
        response = self.client.put(endpoint, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(_('No file was submitted.'), response.json()['icon'])

        self.assertIsNotNone(self.category.icon)
        endpoint = f'/signals/v1/private/categories/{self.parent_category.pk}/icon'
        data = {'icon': ''}
        response = self.client.put(endpoint, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(_('The submitted data was not a file. Check the encoding type on the form.'),
                      response.json()['icon'])

    def test_delete_icon(self):
        """
        The following 2 cases are tested:
         - Delete the icon (category had no icon)
         - Delete the icon (category already had an icon)
        """
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.assertEqual(self.parent_category.icon, None)
        endpoint = f'/signals/v1/private/categories/{self.parent_category.pk}/icon'
        response = self.client.delete(endpoint)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.parent_category.refresh_from_db()
        self.assertIn(self.parent_category.icon, [None, ''])

        self.assertNotEqual(self.category.icon, None)
        endpoint = f'/signals/v1/private/categories/{self.category.pk}/icon'
        response = self.client.delete(endpoint)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.category.refresh_from_db()
        self.assertIn(self.category.icon, [None, ''])

    def test_unauthorized(self):
        """
        User must log in to perform a CRUD operation on the category icon
        """
        self.client.logout()

        endpoint = f'/signals/v1/private/categories/{self.parent_category.pk}/icon'
        data = {'icon': SimpleUploadedFile('image.gif', self.gif_content, content_type='image/gif')}
        response = self.client.put(endpoint, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.delete(endpoint)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        endpoint = f'/signals/v1/private/categories/{self.category.pk}/icon'
        response = self.client.patch(endpoint, data={'icon': ''})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        endpoint = f'/signals/v1/private/categories/{self.category.pk}/icon'
        response = self.client.delete(endpoint)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
