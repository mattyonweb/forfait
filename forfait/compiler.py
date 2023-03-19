from pathlib import Path
from typing import List, Optional

from forfait.astnodes import AstNode
from forfait.parser import Parser
from forfait.ztypes.context import STDLIB, Context


class Compiler:
    def __init__(self, ctx:Optional[Context]=None):
        self.ctx = ctx if ctx is not None else STDLIB

    def compile_source_code(self, source: str):
        typed_ast: List[AstNode]     = Parser(self.ctx).parse(source)
        optimized_ast: List[AstNode] = Optimizer(self.ctx).optimize(typed_ast)
        asm_code                     = CodeGenerator(self.ctx).generate(optimized_ast)
        print(asm_code)