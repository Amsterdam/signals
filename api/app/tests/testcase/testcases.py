from typing import Optional

from rest_framework.test import APITestCase


class JsonAPITestCase(APITestCase):

    def assertResponseFormat(self, left_dict: dict, right_dict: dict, ignore_list_types=False):
        """ Asserts that both dictionaries contain the same keys and value types. Fails when the
        keys in both dictionaries don't match or are associated with different value types.
        Traverses the dictionaries recursively.

        When ignore_list_types is set to False, we check if the items in the list are homogeneous
        and the same for both lists in both dictionaries. Set ignore_list_types to True if you are
        dealing with heterogeneous types.

        Does not necessarily work when dictionaries contain objects (which should not be the case
        when we use this for JSON-deserialised structures)
        """

        self._assert_dicts(left_dict, right_dict, ignore_list_types)

    def _assert_dicts(self, left_dict: dict, right_dict: dict, ignore_list_types=False):
        """ Recursively compares dictionaries according to description in assertResponseFormat """

        for k, v in left_dict.items():
            assert k in right_dict, "Missing key {} in right dictionary".format(k)
            assert isinstance(v,
                              type(right_dict[k])), "Types belonging to key {} to do match".format(
                k)

            if type(v) == dict:
                self._assert_dicts(v, right_dict[k], ignore_list_types)

            if type(v) == list and not ignore_list_types:
                self._assert_list_types(v, right_dict[k])

        assert len(left_dict.keys()) == len(
            right_dict.keys()), "Number of keys in both dicts do not match"

    def _assert_list_types(self, left_list: list, right_list: list):
        left_type = self._assert_list_type(left_list)
        right_type = self._assert_list_type(right_list)

        if left_type is not None and right_type is not None:
            assert left_type == right_type, "List types do not match"

    def _assert_list_type(self, lst: list) -> Optional[type]:
        """ Checks the list is homogeneously typed. Returns the type on success, or None when the
        list is empty (and thus the type could be anything).

        Note: Currently not checking recursively (list within lists)
        """

        if len(lst) == 0:
            return None

        t = type(lst[0])

        for item in lst:
            assert isinstance(item, t), "Expected list item to be of type {}".format(t)

        return t
