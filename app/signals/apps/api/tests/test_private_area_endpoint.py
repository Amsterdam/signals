# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2025 Gemeente Amsterdam
import os
from typing import Any, Final

from django.contrib.auth.models import Permission
from rest_framework import status

from signals.apps.signals.factories import AreaFactory, AreaTypeFactory
from signals.apps.signals.models import Area
from signals.test.utils import SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)


class TestPrivateAreaEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    list_endpoint = '/signals/v1/private/areas/'

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.areas = {}
        self.area_types = AreaTypeFactory.create_batch(5)
        for area_type in self.area_types:
            self.areas[area_type.code] = AreaFactory.create_batch(5, _type=area_type)

        self.list_areas_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema', 'get_signals_v1_private_areas.json')
        )

    def test_get_list(self):
        response = self.client.get(f'{self.list_endpoint}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(25, data['count'])
        self.assertEqual(25, len(data['results']))
        self.assertJsonSchema(self.list_areas_schema, data)

    def test_get_list_filter(self):
        response = self.client.get(f'{self.list_endpoint}?type_code={self.area_types[0].code}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(5, data['count'])
        self.assertEqual(5, len(data['results']))
        self.assertJsonSchema(self.list_areas_schema, data)

    def test_get_list_multiple_filter(self):
        response = self.client.get(f'{self.list_endpoint}?type_code={self.area_types[0].code}'
                                   f'&code={self.areas[self.area_types[0].code][0].code}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(1, data['count'])
        self.assertEqual(1, len(data['results']))
        self.assertJsonSchema(self.list_areas_schema, data)

    def test_get_geography_list(self):
        response = self.client.get(f'{self.list_endpoint}geography/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(25, len(data['features']))

    def test_get_geography_list_filter(self):
        response = self.client.get(f'{self.list_endpoint}geography/?type_code={self.area_types[0].code}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(5, len(data['features']))

    def test_get_geography_list_multiple_filter(self):
        response = self.client.get(f'{self.list_endpoint}geography/?type_code={self.area_types[0].code}'
                                   f'&code={self.areas[self.area_types[0].code][0].code}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(1, len(data['features']))

    def test_get_detail(self):
        response = self.client.get(f'{self.list_endpoint}{self.areas[self.area_types[0].code][0].id}')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_404(self):
        response = self.client.post(f'{self.list_endpoint}1', data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_404(self):
        response = self.client.patch(f'{self.list_endpoint}1', data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_404(self):
        response = self.client.delete(f'{self.list_endpoint}1')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_list_ordered_asc(self):
        area_type_code = self.area_types[0].code

        expected_area_order = list(Area.objects.filter(
            _type__code=area_type_code
        ).order_by(
            'name',
        ).values_list(
            'code',
            flat=True
        ))

        response = self.client.get(f'{self.list_endpoint}?type_code={area_type_code}&ordering=name')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        response_order = [item['code'] for item in data['results']]

        # Compare the order of response data with the expected order of queryset
        self.assertEqual(response_order, expected_area_order)

    def test_get_list_ordered_desc(self):
        area_type_code = self.area_types[0].code

        expected_area_order = list(Area.objects.filter(
            _type__code=area_type_code
        ).order_by(
            '-name',
        ).values_list(
            'code',
            flat=True
        ))

        response = self.client.get(f'{self.list_endpoint}?type_code={area_type_code}&ordering=-name')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        response_order = [item['code'] for item in data['results']]

        # Compare the order of response data with the expected order of queryset
        self.assertEqual(response_order, expected_area_order)


class TestPrivateAreaTypeViewSet(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    URI: Final[str] = '/signals/v1/private/area-types/'

    def test_cannot_list_when_not_authenticated(self) -> None:
        response = self.client.get(self.URI)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_can_list(self) -> None:
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get(self.URI)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_create_when_not_authenticated(self) -> None:
        response = self.client.post(self.URI, data={"name": "test", "code": "test"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_create_when_not_authorized(self) -> None:
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.post(self.URI, data={"name": "test", "code": "test"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_create(self) -> None:
        permission = Permission.objects.get(codename="sia_areatype_write")
        self.sia_read_write_user.user_permissions.add(permission)
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.post(self.URI, data={"name": "test", "code": "test"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestPrivateAreaCreateViewSet(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    URI: Final[str] = "/signals/v1/private/area/"

    def setUp(self) -> None:
        self.area_type = AreaTypeFactory.create()
        self.data = {
            "name": "Centrum-West",
            "code": "GA01",
            "_type": self.area_type.id,
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [
                                120399.937,
                                486481.061
                            ],
                            [
                                120397.763,
                                486495.986
                            ],
                            [
                                120394.512,
                                486509.477
                            ],
                            [
                                120390.061,
                                486522.857
                            ],
                            [
                                120382.702,
                                486540.922
                            ],
                            [
                                120373.11,
                                486560.018
                            ],
                            [
                                120365.274,
                                486572.607
                            ],
                            [
                                120354.043,
                                486587.581
                            ],
                            [
                                120344.786,
                                486597.884
                            ],
                            [
                                120327.159,
                                486613.233
                            ],
                            [
                                120310.408,
                                486630.78
                            ],
                            [
                                120299.375,
                                486644.419
                            ],
                            [
                                120285.378,
                                486664.944
                            ],
                            [
                                120279.565,
                                486685.16
                            ],
                            [
                                120274.181,
                                486710.805
                            ],
                            [
                                120272.252,
                                486723.868
                            ],
                            [
                                120268.883,
                                486768.579
                            ],
                            [
                                120264.494,
                                486790.356
                            ],
                            [
                                120257.14,
                                486813.76
                            ],
                            [
                                120238.436,
                                486857.91
                            ],
                            [
                                120229.74,
                                486877.322
                            ],
                            [
                                120204.307,
                                486909.708
                            ],
                            [
                                120183.434,
                                486941.8
                            ],
                            [
                                120170.877,
                                486965.047
                            ],
                            [
                                120162.038,
                                486984.862
                            ],
                            [
                                120119.992,
                                487101.316
                            ],
                            [
                                120084.052,
                                487235.725
                            ],
                            [
                                120080.679,
                                487254.783
                            ],
                            [
                                120079.982,
                                487270.484
                            ],
                            [
                                120083.034,
                                487284.122
                            ],
                            [
                                120088.051,
                                487298.069
                            ],
                            [
                                120094.255,
                                487310.55
                            ],
                            [
                                120103.729,
                                487324.714
                            ],
                            [
                                120107.012,
                                487328.785
                            ],
                            [
                                120130.165,
                                487350.551
                            ],
                            [
                                120134.764,
                                487356.132
                            ],
                            [
                                120138.93,
                                487362.898
                            ],
                            [
                                120145.03,
                                487375.638
                            ],
                            [
                                120148.336,
                                487385.064
                            ],
                            [
                                120152.247,
                                487404.498
                            ],
                            [
                                120151.787,
                                487443.442
                            ],
                            [
                                120154.594,
                                487478.675
                            ],
                            [
                                120156.541,
                                487493.871
                            ],
                            [
                                120177.764,
                                487490.447
                            ],
                            [
                                120180.209,
                                487505.241
                            ],
                            [
                                120187.657,
                                487529.773
                            ],
                            [
                                120229.119,
                                487635.273
                            ],
                            [
                                120327.714,
                                487887.515
                            ],
                            [
                                120320.582,
                                487890.252
                            ],
                            [
                                120332.326,
                                487919.44
                            ],
                            [
                                120333.857,
                                487918.825
                            ],
                            [
                                120347.241,
                                487953.049
                            ],
                            [
                                120334.056,
                                487958.44
                            ],
                            [
                                120338.664,
                                487970.252
                            ],
                            [
                                120456.205,
                                488271.405
                            ],
                            [
                                120456.979,
                                488278.447
                            ],
                            [
                                120455.76,
                                488284.845
                            ],
                            [
                                120440.848,
                                488312.398
                            ],
                            [
                                120437.563,
                                488322.985
                            ],
                            [
                                120436.909,
                                488329.256
                            ],
                            [
                                120437.329,
                                488337.08
                            ],
                            [
                                120438.677,
                                488343.291
                            ],
                            [
                                120441.569,
                                488350.659
                            ],
                            [
                                120446.141,
                                488358.202
                            ],
                            [
                                120453.339,
                                488365.781
                            ],
                            [
                                120473.341,
                                488378.584
                            ],
                            [
                                120489.162,
                                488391.987
                            ],
                            [
                                120499.657,
                                488403.749
                            ],
                            [
                                120510.984,
                                488420.676
                            ],
                            [
                                120518.581,
                                488436.647
                            ],
                            [
                                120581.443,
                                488599.89
                            ],
                            [
                                120592.842,
                                488628.279
                            ],
                            [
                                120628.794,
                                488711.526
                            ],
                            [
                                120645.353,
                                488742.046
                            ],
                            [
                                120676.292,
                                488802.023
                            ],
                            [
                                120690.074,
                                488828.74
                            ],
                            [
                                120742.854,
                                488950.731
                            ],
                            [
                                120776.514,
                                489065.825
                            ],
                            [
                                120862.566,
                                489041.647
                            ],
                            [
                                120877.921,
                                489037.333
                            ],
                            [
                                121221.108,
                                489069.59
                            ],
                            [
                                121293.336,
                                489076.379
                            ],
                            [
                                121302.524,
                                489041.223
                            ],
                            [
                                121309.016,
                                489042.967
                            ],
                            [
                                121308.518,
                                489044.706
                            ],
                            [
                                121309.55,
                                489059.787
                            ],
                            [
                                121313.21,
                                489078.247
                            ],
                            [
                                121498.253,
                                489095.639
                            ],
                            [
                                121536.251,
                                488898.477
                            ],
                            [
                                121550.576,
                                488836.006
                            ],
                            [
                                121575.174,
                                488756.516
                            ],
                            [
                                121609.805,
                                488671.464
                            ],
                            [
                                121646.637,
                                488602.714
                            ],
                            [
                                121687.288,
                                488536.17
                            ],
                            [
                                121737.82,
                                488465.58
                            ],
                            [
                                121745.144,
                                488457.275
                            ],
                            [
                                121792.93,
                                488403.082
                            ],
                            [
                                121832.176,
                                488366.036
                            ],
                            [
                                121853.001,
                                488346.377
                            ],
                            [
                                121908.281,
                                488299.646
                            ],
                            [
                                121970.138,
                                488258.368
                            ],
                            [
                                121981.428,
                                488250.834
                            ],
                            [
                                122049.267,
                                488210.959
                            ],
                            [
                                122120.496,
                                488175.947
                            ],
                            [
                                122199.444,
                                488146.487
                            ],
                            [
                                122235.462,
                                488135.418
                            ],
                            [
                                122262.93,
                                488127.922
                            ],
                            [
                                122116.843,
                                487894.361
                            ],
                            [
                                122065.791,
                                487810.091
                            ],
                            [
                                122045.505,
                                487745.336
                            ],
                            [
                                121978.387,
                                487695.921
                            ],
                            [
                                121908.361,
                                487477.41
                            ],
                            [
                                121885.329,
                                487401.961
                            ],
                            [
                                121869.478,
                                487349.071
                            ],
                            [
                                121858.841,
                                487352.093
                            ],
                            [
                                121846.39,
                                487351.126
                            ],
                            [
                                121838.05,
                                487348.225
                            ],
                            [
                                121832.489,
                                487343.753
                            ],
                            [
                                121827.896,
                                487337.346
                            ],
                            [
                                121799.368,
                                487274.248
                            ],
                            [
                                121798.039,
                                487266.995
                            ],
                            [
                                121810.93,
                                487261.094
                            ],
                            [
                                121772.194,
                                487189.407
                            ],
                            [
                                121734.944,
                                487124.933
                            ],
                            [
                                121570.358,
                                486848.056
                            ],
                            [
                                121561.071,
                                486825.241
                            ],
                            [
                                121530.353,
                                486772.016
                            ],
                            [
                                121508.898,
                                486737.271
                            ],
                            [
                                121501.871,
                                486729.117
                            ],
                            [
                                121494.772,
                                486722.925
                            ],
                            [
                                121480.023,
                                486718.867
                            ],
                            [
                                121464.917,
                                486716.449
                            ],
                            [
                                121430.313,
                                486714.412
                            ],
                            [
                                121418.374,
                                486714.615
                            ],
                            [
                                121400.228,
                                486714.925
                            ],
                            [
                                121395.144,
                                486712.197
                            ],
                            [
                                121371.771,
                                486687.51
                            ],
                            [
                                121364.267,
                                486679.583
                            ],
                            [
                                121359.691,
                                486676.578
                            ],
                            [
                                121350.308,
                                486672.72
                            ],
                            [
                                121322.858,
                                486672.12
                            ],
                            [
                                121254.361,
                                486674.218
                            ],
                            [
                                121214.661,
                                486680.567
                            ],
                            [
                                121142.586,
                                486699.984
                            ],
                            [
                                121111.429,
                                486716.317
                            ],
                            [
                                121037.134,
                                486810.831
                            ],
                            [
                                121004.68,
                                486852.117
                            ],
                            [
                                120981.404,
                                486840.395
                            ],
                            [
                                120911.911,
                                486801.745
                            ],
                            [
                                120909.031,
                                486746.779
                            ],
                            [
                                120854.933,
                                486713.743
                            ],
                            [
                                120806.442,
                                486687.976
                            ],
                            [
                                120763.42,
                                486662.956
                            ],
                            [
                                120644.532,
                                486596.234
                            ],
                            [
                                120515.616,
                                486521.071
                            ],
                            [
                                120502.325,
                                486513.823
                            ],
                            [
                                120459.98,
                                486490.064
                            ],
                            [
                                120400.18,
                                486458.636
                            ],
                            [
                                120400.7,
                                486465.615
                            ],
                            [
                                120399.937,
                                486481.061
                            ]
                        ]
                    ]
                ]
            }
        }

    def test_cannot_create_when_not_authenticated(self) -> None:
        response = self.client.post(self.URI, data=self.data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_create_when_not_authorized(self) -> None:
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.post(self.URI, data=self.data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_create(self) -> None:
        permission = Permission.objects.get(codename="sia_area_write")
        self.sia_read_write_user.user_permissions.add(permission)
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.post(self.URI, data=self.data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
