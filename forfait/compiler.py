from typing import List, Optional

from forfait.astnodes import AstNode
from forfait.code_generator import CodeGenerator
from forfait.optimizer import Optimizer
from forfait.parser.parser import Parser
from forfait.stdlibs.basic_stdlib import get_stdlib
from forfait.ztypes.context import Context


class Compiler:
    def __init__(self, ctx:Optional[Context]=None):
        self.ctx = ctx if ctx is not None else get_stdlib()

    def compile_source_code(self, source: str):
        typed_ast: List[AstNode]     = Parser(self.ctx).parse(source)
        optimized_ast: List[AstNode] = Optimizer(self.ctx).optimize(typed_ast)
        asm_code                     = CodeGenerator(self.ctx).generate(optimized_ast)
        print(asm_code)



if __name__ == "__main__":
    Compiler().compile_source_code("dup +u8")