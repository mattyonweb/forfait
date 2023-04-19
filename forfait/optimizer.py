import logging
from typing import *
from typing import List

from forfait.astnodes import Sequence, Number, Funcall, AstNode, Funcdef, Quote, Boolean
from forfait.ztypes.context import Context
from forfait.ztypes.ztypes import ZTBase

class PeepholeOptimization:
    def __init__(self, arity: int, checker: Callable, generator: Callable[[List[Funcall]], None]):
        self.checker = checker
        self.generator = generator
        self.arity = arity

    def check(self, stream: List[Funcall]):
        if len(stream) < self.arity:
            return False

        return self.checker(*stream[:self.arity])

    def try_optimization(self, stream: List[Funcall]) -> Optional[Funcall]:
        if len(stream) < self.arity:
            return stream.pop(0)

        if self.check(stream):
            self.generator(stream)
        else:
            return stream.pop(0)


#####################################################

## If:
##   F(F^-1(x)) = x,
## remove F and F^-1
def inverse_of_inverse2_check(top: Funcall, snd: Funcall):
    match top.funcname, snd.funcname:
        case ("swap", "swap") | ("dup", "drop") | ("over", "drop"):
            return True
    return False

def inverse_of_inverse2_do(stream: List[Funcall]):
    stream.pop(0)
    stream.pop(0)

inverse_of_inverse2 = PeepholeOptimization(
    2,
    inverse_of_inverse2_check,
    inverse_of_inverse2_do
)

#######################################################

def compiletime_arithmetic_do(stream: List[Funcall]):
    left, right, op = stream.pop(0), stream.pop(0), stream.pop(0)

    assert isinstance(left, Number)
    assert isinstance(right, Number)

    match op.funcname:
        case "+u8":
            stream.insert(0, Number((left.n + right.n) % 256, ZTBase.U8))
        case "-u8":
            stream.insert(0, Number((left.n - right.n) % 256, ZTBase.U8))
        case "*u8":
            stream.insert(0, Number((left.n * right.n) % 256, ZTBase.U8))
        case "/u8":
            stream.insert(0, Number((left.n // right.n) % 256, ZTBase.U8))
        case "<u8":
            stream.insert(0, Boolean(left.n < right.n))
        case "<=u8":
            stream.insert(0, Boolean(left.n <= right.n))
        case ">u8":
            stream.insert(0, Boolean(left.n > right.n))
        case ">=u8":
            stream.insert(0, Boolean(left.n >= right.n))
        case "==u8":
            stream.insert(0, Boolean(left.n == right.n))
        case "!=u8":
            stream.insert(0, Boolean(left.n != right.n))
        case _:
            raise Exception(f"Optimization on unknown op: {op}")

compiletime_arithmetic = PeepholeOptimization(
    3,
    lambda left, right, op:
        isinstance(left, Number) and isinstance(right, Number) and op.funcname in {
            "+u8", "-u8", "*u8", "/u8", ">u8", ">=u8", "<u8", "<=u8", "==u8", "!=u8"
        },
    compiletime_arithmetic_do
)

##########################################################

stdlib_peeps = [compiletime_arithmetic, inverse_of_inverse2]

##########################################################


class Optimizer:
    def __init__(self, ctx: Context, user_peep_optimizations: Optional[list[PeepholeOptimization]]=None):
        self.ctx = ctx
        self.peep_opts = stdlib_peeps if user_peep_optimizations is None else stdlib_peeps + user_peep_optimizations

    def optimize(self, astnodes: List[AstNode]) -> List[AstNode]:
        optimized = list()

        for node in astnodes:
            optimized_node = self.optimize_astnode(node)

            if optimized_node is not None:
                optimized.append(optimized_node)

        return optimized
        # return [self.optimize_astnode(node) for node in astnodes]

    ##############################################################

    def optimize_astnode(self, node: AstNode) -> Optional[AstNode]:
        """
        Optimize a single ASTNode.
        """
        if isinstance(node, (Number, Boolean)):
            return node
        if isinstance(node, Funcdef):
            return self.optimize_funcdef(node)
        if isinstance(node, Quote):
            return self.optimize_quote(node)
        if isinstance(node, Funcall):
            return node
        if isinstance(node, Sequence):
            return self.optimize_sequence(node)

    def optimize_quote(self, quote: Quote) -> Quote:
        # TODO: se quote è vuota, non ritornare niente
        return Quote(self.optimize_sequence(quote.body))

    def optimize_funcdef(self, fdef: Funcdef) -> Funcdef:
        return Funcdef(fdef.funcname, self.optimize_astnode(fdef.funcbody))

    def optimize_sequence(self, seq: Sequence) -> Sequence:
        funcs: list[Funcall] = [self.optimize_astnode(x) for x in seq.funcs]

        logging.debug(f"Before optimization: {' '.join(str(x) for x in funcs)}")

        while True:
            optimized = self.optimization_round(funcs)
            if optimized == funcs:
                break
            logging.debug(f"Optimization round result: {' '.join(str(x) for x in optimized)}")
            funcs = optimized

        return Sequence(funcs)

    #################################################################

    def optimization_round(self, funcs: list[Funcall]) -> list[Funcall]:
        """
        A single round of optimization on a Sequence of funcall.
        Iterates over all peephole optimizations in self.peeps
        """
        local_copy: list[Funcall] = funcs[:]
        out: list[Funcall] = list()

        # for each peephole optimization...
        for optimization in self.peep_opts:
            # while there are enough funcalls to "sustain" the optimization arity...
            while len(local_copy) >= optimization.arity:
                # out_funcall is the possible name of the function to add to `out`
                out_funcall = optimization.try_optimization(local_copy)

                # no optimization was possible => add first funcall to out:
                if out_funcall is not None:
                    out.append(out_funcall)

            local_copy = out + local_copy # must add also remaining `opt.arity` elements to `out`
            out = list()

        return local_copy

