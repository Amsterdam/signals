from django.contrib.gis.geos import Point

from signals.apps.signals.models import Buurt, Stadsdeel


class AddressGebieden:

    def get_gebieden_for_lat_long(self, lat: float, long: float):
        pnt = Point(long, lat)

        buurt = self._get_buurt_for_point(pnt)
        stadsdeel = self._get_stadsdeel_for_point(pnt)

        buurt_dict = self._buurt_to_dict(buurt) if buurt else {}
        stadsdeel_dict = self._stadsdeel_to_dict(stadsdeel) if stadsdeel else {}

        return {
            "stadsdeel": stadsdeel_dict,
            "buurt": buurt_dict,
        }

    def _buurt_to_dict(self, buurt: Buurt):
        return {
            "code": buurt.vollcode,
            "naam": buurt.naam,
        }

    def _stadsdeel_to_dict(self, stadsdeel: Stadsdeel):
        return {
            "code": stadsdeel.code,
            "naam": stadsdeel.naam,
        }

    def _get_buurt_for_point(self, point: Point):
        return Buurt.objects.filter(wkb_geometry__contains=point).first()

    def _get_stadsdeel_for_point(self, point: Point):
        return Stadsdeel.objects.filter(wkb_geometry__contains=point).first()
