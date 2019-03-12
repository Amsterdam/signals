from django.test import TestCase

from signals.apps.signals.address.gebieden import AddressGebieden


class TestAddressGebieden(TestCase):
    fixtures = ['buurten.json', 'stadsdeel.json', ]

    def test_get_gebieden_for_lat_long(self):
        testcases = [
            {
                # Dam square
                "lat": 52.3737398,
                "long": 4.8950857,
                "result": {
                    "stadsdeel": {
                        "code": "A",
                        "naam": "Centrum",
                    },
                    "buurt": {
                        "code": "A00b",
                        "naam": "Oude Kerk e.o.",
                    },
                },
            },
            {
                # IJburg
                "lat": 52.3584459,
                "long": 4.9898655,
                "result": {
                    "stadsdeel": {
                        "code": "M",
                        "naam": "Oost",
                    },
                    "buurt": {
                        "code": "M35e",
                        "naam": "Haveneiland Noordwest",
                    },
                }
            },
            {
                # Somewhere far away, on the Bahamas
                "lat": 24.5839024,
                "long": -77.9868018,
                "result": {
                    "buurt": {},
                    "stadsdeel": {},
                },
            },
        ]

        address_gebieden = AddressGebieden()

        for testcase in testcases:
            result = address_gebieden.get_gebieden_for_lat_long(testcase["lat"], testcase["long"])

            self.assertEquals(testcase["result"], result)
