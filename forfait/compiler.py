import logging
# logging.basicConfig(level=logging.DEBUG)

from typing import List, Optional

from forfait.astnodes import AstNode
from forfait.code_generator import CodeGenerator
from forfait.optimizer import Optimizer
from forfait.parser.firstphase import FirstPhase
from forfait.ssa.ssa import constant_propagation, CFG
from forfait.stdlibs.basic_stdlib import get_stdlib
from forfait.ztypes.context import Context

class Compiler:
    def __init__(self, ctx:Optional[Context]=None, debug_level=0):
        self.ctx = ctx if ctx is not None else get_stdlib()
        self.debug_level = debug_level

    def _debug(self, required_level: int, s: str):
        if self.debug_level >= required_level:
            print(s)

    def compile_source_code(self, source: str):
        typed_ast: List[AstNode]     = FirstPhase(self.ctx).parse_and_typecheck(source)
        optimized_ast: List[AstNode] = Optimizer(self.ctx).optimize(typed_ast)
        asm_code                     = CodeGenerator(self.ctx).generate(optimized_ast)
        self._debug(1, asm_code)

    def ssify(self, source: str) -> list[CFG]:
        from forfait.ssa.ssa import SSA_ification

        typed_ast: List[AstNode] = FirstPhase(self.ctx).parse_and_typecheck(source)

        cfgs = list()
        for astnode in typed_ast:
            self._debug(1, str(astnode))

            cfg, _ = SSA_ification(astnode)  # TODO: scartare i vstack da un astnode all'altro ti fa perdere qualcosa secondo me
            cfg    = constant_propagation(cfg)
            for cfg_block in cfg.graph_visit():
                self._debug(1, cfg_block)

            cfgs.append(cfg)

        return cfgs
    ###################################################

    def repl_finaltype(self):
        import readline
        while (cmd := input("> ").strip()) != "quit":
            try:
                typed_ast = FirstPhase(self.ctx).parse_and_typecheck(cmd)
                # self.ssify(cmd)
            except Exception as e:
                import traceback
                traceback.print_exc()
            finally:
                self.ctx.reset()




if __name__ == "__main__":
    # Compiler().compile_source_code("1 3 dup 99 u16 101 u16 dup")
    # Compiler().compile_source_code("swap 2 +u8 drop ++u16")
    # Compiler().compile_source_code("swap ++u16 +u16")

    Compiler(debug_level=1).repl_finaltype()

    # 1 99 100 <u8 [| drop |] [| drop |] if