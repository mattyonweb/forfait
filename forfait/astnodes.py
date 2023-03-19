from abc import abstractmethod
from typing import *

from forfait.my_exceptions import ZException
from forfait.ztypes import ZType, type_of_application, Context, ZTFunction


class AstNode:
    @abstractmethod
    def typeof(self, ctx: Context) -> ZType:
        return ZType()


class Funcall:
    def __init__(self, funcname: str, type_: ZTFunction):
        self.funcname: str = funcname
        self.type = type_

    def typeof(self, _: Context) -> ZTFunction:
        return self.type


class Sequence:
    def __init__(self, funcs: List[Funcall]):
        self.funcs = funcs

    def typeof(self, ctx: Context) -> ZType:
        if len(self.funcs) == 0:
            raise ZException("Empty sequence of funcalls has no type")
        if len(self.funcs) == 1:
            return self.funcs[0].typeof(ctx)

        last_type = type_of_application(
            self.funcs[0].typeof(ctx),
            self.funcs[1].typeof(ctx),
            ctx
        )
        for funcall in self.funcs[2:]:
            last_type = type_of_application(
                last_type, funcall.typeof(ctx), ctx
            )
        return last_type


class Funcdef:
    def __init__(self, funcname: str, funcbody: AstNode):
        self.funcname = funcname
        self.funcbody = funcbody

    def typeof(self, ctx: Context) -> ZType:
        return self.funcbody.typeof(ctx)


