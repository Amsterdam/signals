import logging

from rest_framework.exceptions import ValidationError

from signals.apps.api.v1.validation.address.base import (
    AddressValidationUnavailableException,
    NoResultsException
)
from signals.apps.api.v1.validation.address.pdok import PDOKAddressValidation

logger = logging.getLogger(__name__)


class AddressValidationMixin:
    address_validation_class = PDOKAddressValidation

    def get_address_validation(self):
        """
        Return the address validation instance that should be used for validating
        """
        validation_class = self.get_address_validation_class()
        return validation_class()

    def get_address_validation_class(self):
        """
        Return the class to use for the address valdiation.
        Defaults to using `self.address_validation_class`.
        """
        assert self.address_validation_class is not None, (
                "'%s' should either include a `address_validation_class` attribute, "
                "or override the `get_validation_class()` method."
                % self.__class__.__name__
        )
        return self.address_validation_class

    def validate_location(self, location_data):
        """
        Validate location data used in creation and update of Signal instances
        At least the geometrie must be present in the location data
        If the address is present it will be validated against the service defined in the address_validation_class
        """
        # Validate address, but only if it is present in input. SIA must also
        # accept location data without address but with coordinates.
        if 'geometrie' not in location_data:
            raise ValidationError('Coordinate data must be present')

        lon, lat = location_data['geometrie'].coords

        if 'address' in location_data and location_data["address"]:
            try:
                address_validation = self.get_address_validation()
                validated_address = address_validation.validate_address(location_data["address"], lon, lat)

                # Set suggested address from AddressValidation as address and save original address
                # in extra_properties, to correct possible spelling mistakes in original address.
                if 'extra_properties' not in location_data or location_data["extra_properties"] is None:
                    location_data["extra_properties"] = {}

                location_data["extra_properties"]["original_address"] = location_data["address"]
                location_data["address"] = validated_address
                location_data["bag_validated"] = True
            except AddressValidationUnavailableException:
                # Ignore it when the address validation is unavailable. Just save the unvalidated
                # location. Added log a warning.
                logger.warning('Address validation unavailable', stack_info=True)
            except NoResultsException:
                # For now we only log a warning and store the address unvalidated in the database
                logger.warning('Address not found', stack_info=True)
                raise ValidationError({"location": "Niet-bestaand adres."})

        return location_data
