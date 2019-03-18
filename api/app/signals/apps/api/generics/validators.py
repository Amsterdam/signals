from rest_framework.serializers import ValidationError


class NearAmsterdamValidatorMixin:

    def validate_geometrie(self, value):
        fail_msg = 'Location coordinates not anywhere near Amsterdam. (in WGS84)'

        lat_not_in_adam_area = not 50 < value.coords[1] < 55
        lon_not_in_adam_area = not 1 < value.coords[0] < 7

        if lon_not_in_adam_area or lat_not_in_adam_area:
            raise ValidationError(fail_msg)
        return value
