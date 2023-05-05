from unittest import TestCase
from typing import *

from forfait.compiler import Compiler
from forfait.ssa.ssa import *


class TestSSA(TestCase):
    def runtest(self, src: str) -> CFG:
        self.compiler = Compiler(debug_level=0)
        try:
            return self.compiler.ssify(src)[0]
        finally:
            self.compiler.ctx.reset()

    def test_ssa_ification1(self):
        cfg = self.runtest("1 2 3")
        for i in cfg.instructions:
            self.assertIsInstance(i, SSA_Constant)
            self.assertIsInstance(i.const, Number)

    def test_ssa_ification2(self):
        cfg = self.runtest("1 2 3 +u8 +u8 dup 99 <u8 [| dup |] [| dup swap |] if")
        print(cfg.emit_program())

    def test_ssa_ification2_5(self):
        cfg = self.runtest("[| dup dup +u8 +u8 |] test")
        print(cfg.emit_program())