import logging


import copy
from abc import abstractmethod
from typing import Optional

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

    def finally_annotate_quotes(self, ctx: Context):
        pass


##################################################

class Funcall(AstNode):
    def __init__(self, funcname: str, type_: ZTFunction):
        self.funcname: str = funcname
        self.type = type_  # initially retrieved from the STDLIB, then monomorphized if needed
        self.arity_in  = self.type.left.arity()
        self.arity_out = self.type.right.arity()

    def typeof(self, _: Context) -> ZTFunction:
        return self.type

    def __str__(self):
        return self.funcname

    def prettyprint(self, indent=0):
        print(f"{' '*indent}Funcall {self.funcname} :: {self.type}")

    def finally_annotate_quotes(self, ctx: Context):
        subs, order = ctx.ordered_subs()
        for lhs in order:
            if lhs.counter not in subs:  # HACK: TODO: da ripensare eh
                continue

            self.type.substitute_generic(lhs, subs[lhs.counter])

        self.type.left.keep_last_n(self.arity_in)
        self.type.right.keep_last_n(self.arity_out)


##################################################

class Quote(Funcall):
    def __init__(self, body: "Sequence"):
        self.body: Sequence = body
        self.row_generic = ZTRowGeneric("NQ")
        self.funcname = None # ?

        self.type: Optional[ZTFunction] = None
        self.arity_in  = None
        self.arity_out = None

    def typeof(self, ctx: Context) -> ZTFunction:
        if self.type is not None:
             return self.type

        # TODO: credo che usare qui copy() sia un grosso problema.
        #  infatti quando poi devi ricostruire il tipo interno delle funcall nella quote non riesci,
        #  perché ti troverai con delle type variables T_123 internamente identiche ma con hash diversi
        #  (e infati questo è uno dei problemi che hai trovato, che quando aggiungi una sub ti ritrovi cose tipo
        #  T_123 =?= T_123 il che è paradossale, e forse richiede di implementare un eq() fra tipi)
        # TODO: ma poi perché faccio la copy? Immagino sia perché in futuro "taglierò" questi tipi, ma
        #  quando e perche?
        self.type      = ZTFuncHelper(self.row_generic, [], self.row_generic, [copy.deepcopy(self.body.typeof(ctx))])
        self.arity_in  = self.type.left.arity()  # is it always 0 right?
        self.arity_out = self.type.right.arity() # is it always 1 right?

        return self.type

    def typecheck(self, ctx: Context):
        self.body.typecheck(ctx)

    def __str__(self):
        return f"[| " + str(self.body).strip() + " |]"

    def prettyprint(self, indent=0):
        print(f"{' '*indent}Quote: [|")
        self.body.prettyprint(indent+2)

    def finally_annotate_quotes(self, ctx: Context):
        """
        Basically, if you have a program such as:
                42 [| dup |] eval
        for complex reason (which not even I understand completely, at this hour of the night)
        funcalls types inside the Quotation are not substituted with their concrete types; however,
        the "complete" type of the quote is calculated correctly (i.e. if we consider the Quote as a
        black box, you don't need this method; but since the inside of a quotation has to be monomoprhized
        and implemented at some point, you _do_ care about the inner types!)

        This method must be called by the compiler just before the typechecking phase ends.
        It performs again type-checking, using the information on the "complete" type of the quote.

        Think of it as re-calculating the type of
                42 [| dup |] eval
                      ^^^
        knowing that it must be the case that  [| dup |] :: u8 -> u8 u8.
        :return:
        """
        for func in self.body.funcs:
            func.finally_annotate_quotes(ctx)

        super().finally_annotate_quotes(ctx)


##################################################

class ZConstant:
    pass

class Number(Funcall, ZConstant):
    def __init__(self, n: int, t: ZTBase):
        self.n = n
        self.row_generic = ZTRowGeneric("S")
        # self.t = ZTFuncHelper(self.row_generic, [], self.row_generic, [t])
        super().__init__(str(n), ZTFuncHelper(self.row_generic, [], self.row_generic, [t]))

    def typeof(self, _: Context) -> ZTFunction:
        return self.type

    def typecheck(self, ctx: Context):
        pass # TODO: checks of numeric range

    def __str__(self):
        return f"{self.n}"

    def prettyprint(self, indent=0):
        print(f"{' '*indent}Number: {self.n}")

##################################################

class Boolean(Funcall, ZConstant):
    def __init__(self, b: bool):
        self.b = b
        self.row_generic = ZTRowGeneric("S")
        # self.t = ZTFuncHelper(self.row_generic, [], self.row_generic, [ZTBase.BOOL])
        super().__init__(
            str("true" if self.b else "false"),
            ZTFuncHelper(self.row_generic, [], self.row_generic, [ZTBase.BOOL])
        )

    def typeof(self, _: Context) -> ZTFunction:
        return self.type

    def typecheck(self, ctx: Context):
        pass

    def __str__(self):
        return f"{self.b}"

    def prettyprint(self, indent=0):
        print(f"{' '*indent}Boolean: {self.b}")

##################################################

class Sequence(AstNode):
    """
    A sequence of funcalls/quotations/numbers.
    """
    def __init__(self, funcs: list[Funcall]):
        self.funcs: list[Funcall]       = funcs
        self.type: Optional[ZTFunction] = None  #set after first typeof() call, then treated as a singleton

    def typecheck(self, ctx: Context):
        for x in self.funcs:
            x.typecheck(ctx)


    def typeof(self, ctx: Context) -> ZTFunction:
        # if the type was already calculated, then return the old result
        logging.debug(f"Typechecking sequence: {self}")

        if self.type is not None:
            logging.debug(f"Sequence had an already-set type, namely: {self.type}")
            return self.type

        if len(self.funcs) == 0:
            raise ZException("Empty sequence of funcalls has no type")

        if len(self.funcs) == 1:
            out = self.funcs[0].typeof(ctx)
            ctx.inner_type[self.funcs[0]] = out
            return out

        # calculate the type of the first function application
        last_type = type_of_application_rowpoly(
            self.funcs[0].typeof(ctx),
            self.funcs[1].typeof(ctx),
            ctx
        )

        # calculate the type of all the remaining function applications
        for funcall in self.funcs[2:]:
            last_type = type_of_application_rowpoly(
                last_type, funcall.typeof(ctx), ctx
            )

        # at the end of a sequence, the substitution equations are not needed anymore
        # (where would they be needed?)
        # ctx.clear_generic_subs()

        # store the final type of the whole sequence (`copy` is needed, as otherwise
        # it would be cut when adjusting the arity of the types in Context, at the end
        # of the parsing phase)
        self.type = copy.deepcopy(last_type)

        return last_type


    def __str__(self):
        return " ".join([str(f) for f in self.funcs]).strip()

    def prettyprint(self, indent=0):
        print(f"{' '*indent}Sequence:")
        for x in self.funcs:
            x.prettyprint(indent+2)

    def finally_annotate_quotes(self, ctx: Context):
        for funcall in self.funcs:
            funcall.finally_annotate_quotes(ctx)

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

    def finally_annotate_quotes(self, ctx: Context):
        for node in self.funcbody:
            node.finally_annotate_quotes(ctx)
