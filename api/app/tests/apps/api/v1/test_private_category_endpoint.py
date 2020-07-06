from django.contrib.auth.models import Permission
from rest_framework import status

from signals.apps.signals.models import CategoryDepartment
from tests.apps.signals.factories import CategoryFactory, DepartmentFactory, ParentCategoryFactory
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestPrivateCategoryEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        sia_category_write_permission = Permission.objects.get(codename='sia_category_write')
        self.sia_read_write_user.user_permissions.add(sia_category_write_permission)

        self.parent_category = ParentCategoryFactory.create()

        CategoryFactory.create_batch(5, parent=self.parent_category)
        self.parent_category.refresh_from_db()

        super(TestPrivateCategoryEndpoint, self).setUp()

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

    def test_list_categories(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = '/signals/v1/private/categories/?page_size=1000'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['count'], 166)
        self.assertEqual(len(data['results']), 166)

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

    def test_get_second_child_category(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        category = self.parent_category.children.first()

        department = DepartmentFactory.create(is_intern=False)
        category.departments.add(department, through_defaults={'is_responsible': False, 'can_view': True})

        department = DepartmentFactory.create(is_intern=True)
        category.departments.add(department, through_defaults={'is_responsible': True, 'can_view': True})

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
        }

        response = self.client.patch(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        category.refresh_from_db()
        self._assert_category_data(category=category, data=response.json())

    def test_post_category(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = f'/signals/v1/private/categories/'
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_category(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        url = f'/signals/v1/private/categories/{self.parent_category.pk}'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_not_logged_in(self):
        url = f'/signals/v1/private/categories/'

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
        self.assertIn('Naam wijziging:\n Patched name again', change_log_data['action'])
        self.assertIn('Status wijziging:\n Inactief', change_log_data['action'])

        change_log_data = response_data[1]
        self.assertEqual(change_log_data['what'], 'UPDATED_CATEGORY')
        self.assertIsNone(change_log_data['description'])
        self.assertEqual(change_log_data['who'], self.sia_read_write_user.username)
        self.assertIn('Naam wijziging:\n Patched name', change_log_data['action'])

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
        self.assertIn('E-mail tekst wijziging:\n Patched handling message', change_log_data['action'])
