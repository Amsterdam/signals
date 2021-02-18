from signals.apps.signals.factories import DepartmentFactory
from signals.apps.users.factories import UserFactory
from tests.test import SignalsBaseApiTestCase


class TestUserProfileDepartmentFilter(SignalsBaseApiTestCase):
    LIST_ENDPOINT = '/signals/v1/private/users/'

    def _request_filter_users(self, filter_params: dict):
        """ Does a filter request and returns the signal ID's present in the request """
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(self.LIST_ENDPOINT, data=filter_params)

        self.assertEqual(200, resp.status_code)

        resp_json = resp.json()
        ids = [res["id"] for res in resp_json["results"]]

        self.assertEqual(resp_json["count"], len(ids))

        return ids

    def setUp(self):
        self.dep1 = DepartmentFactory.create()
        self.dep2 = DepartmentFactory.create()
        self.user1 = UserFactory.create()
        self.user2 = UserFactory.create()
        self.user3 = UserFactory.create()

        self.user1.profile.departments.add(self.dep1, self.dep2)
        self.user2.profile.departments.add(self.dep2)

    def test_filter_user_profile_department(self):
        # all (implicit admin user)
        result_ids = self._request_filter_users({})
        self.assertEqual(3 + 1, len(result_ids))

        # filter on dep1 code
        result_ids = self._request_filter_users({'profile_department_code': f'{self.dep1.code}'})
        self.assertEqual(1, len(result_ids))
        self.assertTrue(self.user1.id in result_ids)

        # filter on dep2 code
        result_ids = self._request_filter_users({'profile_department_code': f'{self.dep2.code}'})
        self.assertEqual(2, len(result_ids))
        self.assertTrue(self.user1.id in result_ids)
        self.assertTrue(self.user2.id in result_ids)

        # mutiple choice
        result_ids = self._request_filter_users({'profile_department_code': [self.dep1.code, self.dep2.code]})
        self.assertEqual(2, len(result_ids))
        self.assertTrue(self.user1.id in result_ids)
        self.assertTrue(self.user2.id in result_ids)

        # TODO FIXME: filter on non-assigned
        # result_ids = self._request_filter_users({'profile_department_code': 'null'})
        # self.assertEqual(1, len(result_ids))
        # self.assertTrue(self.user3.id in result_ids)
