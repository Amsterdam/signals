# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
class AreaLoader:
    PROVIDES: list[str] = []  # override, make list of string dataset names

    def __init__(self, type_string: str):
        # type_string takes a value from the self.PROVIDES list, and is passed
        # when the AreaLoader class is instantiated. When overridden this
        # initializer should also make sure that the desired AreaType is
        # present in the database.

        raise NotImplementedError

    def load(self) -> None:
        # Load the actual data and store it as Area instance.
        raise NotImplementedError
