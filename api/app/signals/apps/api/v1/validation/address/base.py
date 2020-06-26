class AddressValidationUnavailableException(Exception):
    pass


class NoResultsException(Exception):
    pass


class BaseAddressValidation:
    address_validation_url = None

    def _search(self, address, *args, **kwargs):
        raise NotImplementedError('The search functionality should be implemented derived class')

    def _search_result_to_address(self, result):
        """
        If specific mapping is needed this functionality can be overwritten in the derived class
        """
        return result

    def validate_address(self, address, *args, **kwargs):
        results = self._search(address, *args, **kwargs)
        if len(results) == 0:
            raise NoResultsException()
        return self._search_result_to_address(results[0])
