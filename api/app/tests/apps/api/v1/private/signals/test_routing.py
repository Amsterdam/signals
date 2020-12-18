from django.contrib.auth.models import Permission
from rest_framework import status

from signals.apps.signals.factories import (
    CategoryFactory,
    DepartmentFactory,
    ParentCategoryFactory,
    SignalFactory
)
from tests.test import SIAReadUserMixin, SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestSignalEndpointRouting(SIAReadWriteUserMixin, SIAReadUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        self.list_endpoint = '/signals/v1/private/signals/'
        self.detail_endpoint = '/signals/v1/private/signals/{pk}'
        self.subcategory_url_pattern = '/signals/v1/public/terms/categories/{}/sub_categories/{}'
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

        # test signals
        self.signal = SignalFactory.create()
        self.department = DepartmentFactory.create()

    def test_routing_add_remove(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'routing_departments': [
                {
                    'id': self.department.id
                }
            ]
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()
        self.assertEqual(self.signal.routing_assignment.departments.count(), 1)

        # remove routing
        data = {
            'routing_departments': []
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()
        self.assertEqual(self.signal.routing_assignment.departments.count(), 0)

    def test_routing_user_add_remove(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'routing_departments': [
                {
                    'id': self.department.id
                }
            ]
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()

        data = {
            'assigned_user_id': self.sia_read_write_user.id
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()
        self.assertEqual(self.signal.user_assignment.user.id, self.sia_read_write_user.id)

        # remove user assignment
        data = {
            'assigned_user_id': None
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()
        self.assertEqual(self.signal.user_assignment.user, None)

    def test_routing_add_and_check_user(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        read_client = self.client_class()
        read_client.force_authenticate(user=self.sia_read_user)

        response = read_client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 0)

        response = read_client.get(self.detail_endpoint.format(pk=self.signal.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'routing_departments': [
                {
                    'id': self.department.id
                }
            ]
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()

        # add user to department
        self.sia_read_user.profile.departments.add(self.department)

        response = read_client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 1)

        response = read_client.get(self.detail_endpoint.format(pk=self.signal.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_routing_remove_and_check_user(self):
        # adds routing to signal, add user (from dept)
        # change to another department -> user should be removed
        self.client.force_authenticate(user=self.sia_read_write_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'routing_departments': [
                {
                    'id': self.department.id
                }
            ]
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()

        # add user to department
        self.sia_read_user.profile.departments.add(self.department)

        # assign user
        data = {
            'assigned_user_id': self.sia_read_write_user.id
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['assigned_user_id'], self.sia_read_write_user.id)

        new_department = DepartmentFactory.create()
        data = {
            'routing_departments': [
                {
                    'id': new_department.id
                }
            ]
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsNone(data['assigned_user_id'])

        self.signal.refresh_from_db()
        self.assertEqual(self.signal.user_assignment, None)

    def test_routing_change_category_and_check_user_and_routing(self):
        # adds routing to signal, add user (from dept)
        # change category assignment -> user, routing assignment should be removed
        self.client.force_authenticate(user=self.sia_read_write_user)

        detail_endpoint = self.detail_endpoint.format(pk=self.signal.id)
        data = {
            'routing_departments': [
                {
                    'id': self.department.id
                }
            ]
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.signal.refresh_from_db()

        # add user to department
        self.sia_read_user.profile.departments.add(self.department)

        new_parentcategory = ParentCategoryFactory.create()
        new_subcategory = CategoryFactory.create(
            parent=new_parentcategory,
            departments=[self.department],
        )

        link_subcategory = self.subcategory_url_pattern.format(
            new_parentcategory.slug, new_subcategory.slug
        )

        data = {
            'category': {
                'text': 'change cat test',
                'category_url': link_subcategory
            }
        }
        response = self.client.patch(detail_endpoint, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsNone(data['assigned_user_id'])

        self.signal.refresh_from_db()
        self.assertEqual(self.signal.user_assignment, None)
        self.assertEqual(self.signal.routing_assignment, None)
