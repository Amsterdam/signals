from django.contrib.auth.models import Permission
from rest_framework.test import APITestCase

from signals.apps.signals import permissions, workflow
from signals.apps.signals.models import Priority
from tests.apps.signals.factories import (
    CategoryAssignmentFactory,
    SignalFactory,
    SubCategoryFactory
)
from tests.apps.users.factories import UserFactory


class TestCategoryPermissions(APITestCase):
    """
    This class tests the category permissions. A user can only see/edit signals he has access to.
    Category permission checks will be skipped for users that have the SIA_BACKOFFICE permission.


    endpoint                            sia_backoffice   limited access

    v0
    all auth endpoints                     full access   no access

    v1
    GET /signals/v1/private/signals        full access   only signals in assigned categories
    GET /signals/v1/private/signals/{id}   full access   only signals from assigned categories
    PATCH /signals/v1/private/signals/{id} full_access   only signals from assigned categories
    PATCH /signals/v1/private/signals/{id} full access   do not move signal to not-assigned category
    """

    signals = []
    categories = []
    assigned_categories = []
    assigned_signals = []
    user = None

    class PermissionTest:
        user = None
        all_signals = None
        all_categories = None
        test_class = None

        # Default everything closed
        v0_access = False
        signals_access = []
        signals_no_access = []
        categories_access = []
        categories_no_access = []

        location = {
            "geometrie": {
                "type": "Point",
                "coordinates": [
                    4.898466,
                    52.361585
                ]
            },
            "stadsdeel": "A",
            "buurt_code": "aaa1",
            "address": {},
            "extra_properties": {}
        }

        def __init__(self, user, signals, categories, test_class):
            self.user = user
            self.all_signals = signals
            self.all_categories = categories
            self.test_class = test_class

        def should_have_v0_access(self, v0_access: bool = True):
            self.v0_access = v0_access

        def should_have_access_to_signals(self, signals: list):
            self.signals_access = signals
            self.signals_no_access = self._list_difference(self.all_signals, self.signals_access)

        def should_have_access_to_categories(self, categories: list):
            self.categories_access = categories
            self.categories_no_access = self._list_difference(self.all_categories,
                                                              self.categories_access)

        def execute(self):
            self.test_class.client.force_authenticate(user=self.user)

            self._test_v0_access()
            self._test_v1_get_signals()
            self._test_v1_get_signal_by_id()
            self._test_v1_update_signals_in_category()
            self._test_v1_update_signals_move_to_other_category()

        def _list_difference(self, left: list, right: list):
            return [item for item in left if item not in right]

        def _test_get_endpoint(self, endpoint: str, expected_status_code: int):
            response = self.test_class.client.get(endpoint)
            self.test_class.assertEquals(expected_status_code, response.status_code)
            return response

        def _test_post_endpoint(self, endpoint: str, data: dict, expected_status_code: int):
            response = self.test_class.client.post(endpoint, data, format='json')
            self.test_class.assertEquals(expected_status_code, response.status_code)
            return response

        def _test_patch_endpoint(self, endpoint: str, data: dict, expected_status_code: int):
            response = self.test_class.client.patch(endpoint, data)
            self.test_class.assertEquals(expected_status_code, response.status_code)
            return response

        def _test_v0_access(self):
            # Expected status codes
            post_status_code = 201 if self.v0_access else 403
            get_status_code = 200 if self.v0_access else 403

            # Test that user has access to all v0 endpoints, or to none

            response = self._test_get_endpoint('/signals/auth/signal/', get_status_code)

            if get_status_code == 200:
                # Check response
                self.test_class.assertEquals(len(self.all_signals), len(response.json()['results']))

            for signal in self.all_signals:
                self._test_get_endpoint('/signals/auth/signal/{}/'.format(signal.id),
                                        get_status_code)

            for signal in self.all_signals:
                status = {
                    '_signal': signal.id,
                    'state': workflow.AFWACHTING,
                }

                self._test_post_endpoint('/signals/auth/status/', status, post_status_code)

                location = self.location
                location['_signal'] = signal.id

                self._test_post_endpoint('/signals/auth/location/', location, post_status_code)

                category = {
                    '_signal': signal.id,
                    'main': 'Overlast op het water',
                    'sub': 'Overlast op het water - snel varen',
                }

                self._test_post_endpoint('/signals/auth/category/', category, post_status_code)

                note = {
                    '_signal': signal.id,
                    'text': 'Test note',
                }

                self._test_post_endpoint('/signals/auth/note/', note, post_status_code)

                priority = {
                    '_signal': signal.id,
                    'priority': Priority.PRIORITY_HIGH,
                }

                self._test_post_endpoint('/signals/auth/priority/', priority, post_status_code)

        def _test_v1_get_signals(self):
            # Test result of GET /signals/v1/private/signals. Should contain signals in
            # assigned_signals and not the others
            pass

        def _test_v1_get_signal_by_id(self):
            # Test
            pass

        def _test_v1_update_signals_in_category(self):
            # Test we can only update signals in our own categories
            pass

        def _test_v1_update_signals_move_to_other_category(self):
            # Test we can only move signals between own categories
            pass

    def setUp(self):
        """
        Method creates a number of categories and signals. Part of the categories and signals will
        be added to the 'assigned' lists. These lists should be used to assign permissions to the
        user.

        :return:
        """
        self.signals = []
        self.assigned_signals = []
        self.categories = [SubCategoryFactory.create() for _ in range(5)]
        self.assigned_categories = []

        for idx, category in enumerate(self.categories):
            assign = idx % 2 == 0

            if assign:
                self.assigned_categories.append(category)

            for _ in range(5):
                signal = SignalFactory.create()
                category_assignment = CategoryAssignmentFactory(_signal=signal,
                                                                sub_category=category)
                signal.category_assignment = category_assignment
                signal.save()
                self.signals.append(signal)

                if assign:
                    self.assigned_signals.append(signal)

    def _get_ids(self, obj_list):
        return [o.pk for o in obj_list]

    def _user_add_endpoint_specific_v0_endpoint_permissions(self, user):
        user.user_permissions.add(Permission.objects.get(codename='add_note'))
        user.user_permissions.add(Permission.objects.get(codename='add_priority'))
        user.user_permissions.add(Permission.objects.get(codename='add_location'))
        user.user_permissions.add(Permission.objects.get(codename='add_categoryassignment'))
        user.user_permissions.add(Permission.objects.get(codename='add_status'))

    def test_sia_no_permissions(self):
        """ User without backoffice permissions should not have v0 access """
        no_backoffice_permissions_user = UserFactory.create()
        self._user_add_endpoint_specific_v0_endpoint_permissions(no_backoffice_permissions_user)

        test = self.__class__.PermissionTest(no_backoffice_permissions_user, self.signals,
                                             self.categories, self)
        test.should_have_access_to_categories([])
        test.should_have_access_to_signals([])
        test.should_have_v0_access(False)

        test.execute()

    def test_sia_backoffice_permission(self):
        """ User with backoffice permissions should have full v0 access. """
        backoffice_permission = Permission.objects.get(codename=permissions.SIA_BACKOFFICE)
        backoffice_user = UserFactory.create()
        backoffice_user.user_permissions.add(backoffice_permission)
        self._user_add_endpoint_specific_v0_endpoint_permissions(backoffice_user)

        test = self.__class__.PermissionTest(backoffice_user, self.signals, self.categories, self)
        test.should_have_access_to_categories(self.categories)
        test.should_have_access_to_signals(self.signals)
        test.should_have_v0_access()

        test.execute()

    def test_permission_test_class(self):
        pass
