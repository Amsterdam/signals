# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import pytest
from pytest_bdd import parsers, then
from rest_framework.response import Response
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@then(parsers.parse('the response status code should be {status_code:d}'))
def then_status_code(status_code: int, response: Response) -> None:
    assert response.status_code == status_code
