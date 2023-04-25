from typing import List, Optional

from forfait.astnodes import AstNode
from forfait.code_generator import CodeGenerator
from forfait.optimizer import Optimizer
from forfait.parser.firstphase import FirstPhase
from forfait.stdlibs.basic_stdlib import get_stdlib
from forfait.ztypes.context import Context


class Compiler:
    def __init__(self, ctx:Optional[Context]=None):
        self.ctx = ctx if ctx is not None else get_stdlib()

    def compile_source_code(self, source: str):
        typed_ast: List[AstNode]     = FirstPhase(self.ctx).parse_and_typecheck(source)
        optimized_ast: List[AstNode] = Optimizer(self.ctx).optimize(typed_ast)
        asm_code                     = CodeGenerator(self.ctx).generate(optimized_ast)
        print(asm_code)

    def repl_finaltype(self):
        import readline
        while (cmd := input("> ").strip()) != "quit":
            try:
                typed_ast = FirstPhase(self.ctx).parse_and_typecheck(cmd)
                print(typed_ast[0].typeof(self.ctx))
            except Exception as e:
                import traceback
                traceback.print_exc()
            finally:
                self.ctx.reset()



if __name__ == "__main__":
    # Compiler().compile_source_code("1 3 dup 99 u16 101 u16 dup")
    # Compiler().compile_source_code("swap 2 +u8 drop ++u16")
    # Compiler().compile_source_code("swap ++u16 +u16")

    Compiler().repl_finaltype()