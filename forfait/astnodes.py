from abc import abstractmethod
# from typing import *

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

    def prettyprint(self, indent=0):
        pass

##################################################

class Funcall(AstNode):
    def __init__(self, funcname: str, type_: ZTFunction):
        self.funcname: str = funcname
        self.type = type_

    def typeof(self, _: Context) -> ZTFunction:
        return self.type

    def __str__(self):
        return self.funcname

    def prettyprint(self, indent=0):
        print(f"{' '*indent}Funcall {self.funcname} :: {self.type}")


##################################################

class Quote(Funcall):
    def __init__(self, body: "Sequence"):
        self.body = body
        self.row_generic = ZTRowGeneric("NQ")
        self.funcname = None

    def typeof(self, ctx: Context) -> ZTFunction:
        return ZTFuncHelper(self.row_generic, [], self.row_generic, [self.body.typeof(ctx)])
        # return ZTFunction([], [self.body.typeof(ctx)])

    def typecheck(self, ctx: Context):
        self.body.typecheck(ctx)

    def __str__(self):
        return f"[| " + str(self.body).strip() + " |]"

    def prettyprint(self, indent=0):
        print(f"{' '*indent}Quote: [|")
        self.body.prettyprint(indent+2)


##################################################

class Number(Funcall):
    def __init__(self, n: int, t: ZTBase):
        self.n = n
        self.row_generic = ZTRowGeneric("S")
        self.t = ZTFuncHelper(self.row_generic, [], self.row_generic, [t])
        super().__init__(str(n), self.t)

    def typeof(self, _: Context) -> ZTFunction:
        return self.t

    def typecheck(self, ctx: Context):
        pass # TODO: checks of numeric range

    def __str__(self):
        return f"{self.n}"

    def prettyprint(self, indent=0):
        print(f"{' '*indent}Number: {self.n}")

##################################################

class Boolean(Funcall):
    def __init__(self, b: bool):
        self.b = b
        self.row_generic = ZTRowGeneric("S")
        self.t = ZTFuncHelper(self.row_generic, [], self.row_generic, [ZTBase.BOOL])
        super().__init__(str("true" if self.b else "false"), self.t)

    def typeof(self, _: Context) -> ZTFunction:
        return self.t

    def typecheck(self, ctx: Context):
        pass

    def __str__(self):
        return f"{self.b}"

    def prettyprint(self, indent=0):
        print(f"{' '*indent}Boolean: {self.b}")

##################################################

class Sequence(AstNode):
    def __init__(self, funcs: list[Funcall]):
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

    def prettyprint(self, indent=0):
        print(f"{' '*indent}Sequence:")
        for x in self.funcs:
            x.prettyprint(indent+2)
##################################################

class Funcdef(AstNode):
    def __init__(self, funcname: str, funcbody: AstNode):
        self.funcname = funcname
        self.funcbody = funcbody

    def typeof(self, ctx: Context) -> ZType:
        return self.funcbody.typeof(ctx)

    def __str__(self):
        return f": {self.funcname} {self.funcbody} ;"

    def prettyprint(self, indent=0):
        print(f"{' '*indent}Funcdef: {self.funcname}")
        self.funcbody.prettyprint(indent+2)

