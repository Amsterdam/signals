class CaseNotCreatedException(Exception):
    def __init__(self):
        message = "Case could not be created."
        super().__init__(message)


class DocumentNotCreatedException(Exception):
    def __init__(self):
        message = "Document could not be created."
        super().__init__(message)
