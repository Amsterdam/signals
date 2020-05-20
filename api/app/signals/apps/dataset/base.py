class AreaLoader:
    PROVIDES = []  # override, make list of string dataset names

    def __init__(self, type_string):
        # type_string takes a value from the self.PROVIDES list, and is passed
        # when the AreaLoader class is instantiated. When overridden this
        # initializer should also make sure that the desised AreaType is
        # present in the database.

        raise NotImplementedError

    def load(self):
        # Load the actual data and store it as Area instance.
        raise NotImplementedError
