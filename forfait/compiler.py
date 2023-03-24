from pathlib import Path
from typing import List, Optional

from forfait.astnodes import AstNode, Sequence
from forfait.parser import Parser
from forfait.stdlibs.basic_stdlib import get_stdlib
from forfait.ztypes.context import Context


# class Optimizer:
#     def __init__(self, ctx: Context):
#         self.ctx = ctx
#
#     def optimize(self, astnodes: List[AstNode]):
#         for node in astnodes:
#             self.optimize_astnode(node)
#
#     def optimize_astnode(self, node: AstNode):
#         if isinstance(node, Sequence):
#


class Compiler:
    def __init__(self, ctx:Optional[Context]=None):
        self.ctx = ctx if ctx is not None else get_stdlib()

    def compile_source_code(self, source: str):
        typed_ast: List[AstNode]     = Parser(self.ctx).parse(source)
        optimized_ast: List[AstNode] = Optimizer(self.ctx).optimize(typed_ast)
        asm_code                     = CodeGenerator(self.ctx).generate(optimized_ast)
        print(asm_code)