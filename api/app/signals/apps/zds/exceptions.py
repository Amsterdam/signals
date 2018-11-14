class CaseNotCreatedException(Exception):
    def __init__(self):
        message = "Case could not be created."
        super().__init__(message)


class DocumentNotCreatedException(Exception):
    def __init__(self):
        message = "Document could not be created."
        super().__init__(message)


class CaseConnectionException(Exception):
    def __init__(self):
        message = "Case could not be connected to the Signal."
        super().__init__(message)


class StatusNotCreatedException(Exception):
    def __init__(self):
        message = "Case Status could not be created."
        super().__init__(message)


class DocumentConnectionException(Exception):
    def __init__(self):
        message = "Document could not be connected to the Case."
        super().__init__(message)
