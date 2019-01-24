from typing import List, Tuple

from rest_framework.test import APITestCase

from .testcases import JsonAPITestCase


class TestJsonAPITestCase(APITestCase):
    json_api_testcase = JsonAPITestCase()

    def test_assert_list_type(self):
        self.assertEquals(int, self.json_api_testcase._assert_list_type([1, 2, 3]))
        self.assertEquals(str, self.json_api_testcase._assert_list_type(["a", "b", "c"]))
        self.assertEquals(None, self.json_api_testcase._assert_list_type([]))

        self.assertRaises(AssertionError, self.json_api_testcase._assert_list_type, [1, "a", 3])
        self.assertRaises(AssertionError, self.json_api_testcase._assert_list_type, [True, 3, "b"])

    def test_assert_list_types(self):
        self.json_api_testcase._assert_list_types([1, 3, 4], [2, 4, 5])
        self.json_api_testcase._assert_list_types([], [1, 2])
        self.json_api_testcase._assert_list_types(["a", "b"], [])
        self.json_api_testcase._assert_list_types([], [])
        self.json_api_testcase._assert_list_types([True], [False])

        self.assertRaises(AssertionError, self.json_api_testcase._assert_list_types, [1, 3],
                          [False])

    def test_assertResponseFormat(self):

        for dict_a, dict_b in self._get_test_assertResponseFormat_success_testcases():
            self.json_api_testcase.assertResponseFormat(dict_a, dict_b)

        for dict_a, dict_b in self._get_test_assertResponseFormat_fail_testcases():
            self.assertRaises(AssertionError, self.json_api_testcase.assertResponseFormat, dict_a,
                              dict_b)

        for dict_a, dict_b in self._get_test_assertResponseFormat_testcases_list_types():
            self.json_api_testcase.assertResponseFormat(dict_a, dict_b, True)

        for dict_a, dict_b in self._get_test_assertResponseFormat_testcases_list_types():
            self.assertRaises(AssertionError, self.json_api_testcase.assertResponseFormat, dict_a,
                              dict_b)

    def _get_test_assertResponseFormat_success_testcases(self) -> List[Tuple[dict, dict]]:
        testcases = [
            (
                {
                    "stringkey": "stringval",
                    "subdict": {
                        "intkey": 84024024,
                        "float": 8.4,
                        "subsubdict": {
                            "bool": True,
                        },
                    },
                },

                {
                    "stringkey": "somestringvalue",
                    "subdict": {
                        "intkey": 0,
                        "float": .4,
                        "subsubdict": {
                            "bool": False,
                        },
                    },
                },

            ),
        ]

        return testcases

    def _get_test_assertResponseFormat_fail_testcases(self) -> List[Tuple[dict, dict]]:
        testcases = [
            (
                {
                    "stringkey": "stringval",
                    "subdict": {
                        "intkey": 84024024,
                        "float": 8.4,
                        "subsubdict": {
                            "bool": "True",
                        },
                    },
                },

                {
                    "stringkey": "somestringvalue",
                    "subdict": {
                        "intkey": 0,
                        "float": .4,
                        "subsubdict": {
                            "bool": False,
                        },
                    },
                },
            ),
            (
                {
                    "stringkey": "stringval",
                    "subdict": {
                        "intkey": 84024024,
                        "float": 8.4,
                        "subsubdict": {
                            "bool": "True",
                        },
                    },
                },

                {
                    "stringkey": "somestringvalue",
                    "subdict": ["some list which isn't a dict"],
                },
            ),
        ]

        return testcases

    def _get_test_assertResponseFormat_testcases_list_types(self) -> List[Tuple[dict, dict]]:
        testcases = [
            (
                {
                    "stringkey": "stringval",
                    "subdict": {
                        "intkey": 84024024,
                        "float": 8.4,
                        "subsubdict": {
                            "bool": True,
                            "listofints": []
                        },
                    },
                },

                {
                    "stringkey": "somestringvalue",
                    "subdict": {
                        "intkey": 0,
                        "float": .4,
                        "subsubdict": {
                            "bool": False,
                            "listofints": ["a", True]
                        },
                    },
                },

            ),
            (
                {
                    "stringkey": "stringval",
                    "subdict": {
                        "intkey": 84024024,
                        "float": 8.4,
                        "subsubdict": {
                            "bool": True,
                            "listofints": [2, "a", True]
                        },
                    },
                },

                {
                    "stringkey": "somestringvalue",
                    "subdict": {
                        "intkey": 0,
                        "float": .4,
                        "subsubdict": {
                            "bool": False,
                            "listofints": ["a", "b"]
                        },
                    },
                },

            ),
            (
                {
                    "stringkey": "stringval",
                    "subdict": {
                        "intkey": 84024024,
                        "float": 8.4,
                        "subsubdict": {
                            "bool": True,
                            "listofints": [2, 4, 0, 4, 3]
                        },
                    },
                },

                {
                    "stringkey": "somestringvalue",
                    "subdict": {
                        "intkey": 0,
                        "float": .4,
                        "subsubdict": {
                            "bool": False,
                            "listofints": ["a", "b"]
                        },
                    },
                },

            ),
        ]

        return testcases
