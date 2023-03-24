from abc import abstractmethod
from typing import *

from forfait.my_exceptions import ZException
from forfait.ztypes.context import Context
from forfait.ztypes.ztypes import ZType, type_of_application_rowpoly, ZTFunction, ZTFuncHelper, ZTRowGeneric
from forfait.ztypes.ztypes import ZTBase


class AstNode:
    @abstractmethod
    def typeof(self, ctx: Context) -> ZType:
        return ZType()

    def typecheck(self, ctx: Context):
        return

##################################################

class Funcall(AstNode):
    def __init__(self, funcname: str, type_: ZTFunction):
        self.funcname: str = funcname
        self.type = type_

    def typeof(self, _: Context) -> ZTFunction:
        return self.type

    def __str__(self):
        return self.funcname

##################################################

class Quote(Funcall):
    def __init__(self, body: AstNode):
        self.body = body
        self.row_generic = ZTRowGeneric("NQ")

    def typeof(self, ctx: Context) -> ZTFunction:
        return ZTFuncHelper(self.row_generic, [], self.row_generic, [self.body.typeof(ctx)])
        # return ZTFunction([], [self.body.typeof(ctx)])

    def typecheck(self, ctx: Context):
        self.body.typecheck(ctx)

    def __str__(self):
        return f"[| " + str(self.body).strip() + " |]"

##################################################

class Number(Funcall):
    def __init__(self, n: int, t: ZTBase):
        self.n = n
        self.row_generic = ZTRowGeneric("S")
        self.t = ZTFuncHelper(self.row_generic, [], self.row_generic, [t])

    def typeof(self, _: Context) -> ZTFunction:
        return self.t

    def typecheck(self, ctx: Context):
        pass # TODO: checks of numeric range

    def __str__(self):
        return f"{self.n}"

##################################################

class Sequence(AstNode):
    def __init__(self, funcs: List[Funcall]):
        self.funcs = funcs

    def typecheck(self, ctx: Context):
        for x in self.funcs:
            x.typecheck(ctx)

    def typeof(self, ctx: Context) -> ZType:
        if len(self.funcs) == 0:
            raise ZException("Empty sequence of funcalls has no type")
        if len(self.funcs) == 1:
            out = self.funcs[0].typeof(ctx)
            return out

        last_type = type_of_application_rowpoly(
            self.funcs[0].typeof(ctx),
            self.funcs[1].typeof(ctx),
            ctx
        )

        for funcall in self.funcs[2:]:
            ctx.clear_generic_subs()
            last_type = type_of_application_rowpoly(
                last_type, funcall.typeof(ctx), ctx
            )

        ctx.clear_generic_subs()
        return last_type

    def __str__(self):
        return " ".join([str(f) for f in self.funcs]).strip()

##################################################

class Funcdef(AstNode):
    def __init__(self, funcname: str, funcbody: AstNode):
        self.funcname = funcname
        self.funcbody = funcbody

    def typeof(self, ctx: Context) -> ZType:
        return self.funcbody.typeof(ctx)

    def __str__(self):
        return f": {self.funcname} {self.funcbody} ;"

