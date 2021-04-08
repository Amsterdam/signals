# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from abc import ABC, abstractmethod


class Evaluator(ABC):
    @abstractmethod
    def evaluate(self, ctx):
        pass

    def resolve(self, ctx, ident):
        if ident in ctx:
            return ctx[ident]
        else:
            raise Exception("Could not resolve ident: '{}'".format(ident))
