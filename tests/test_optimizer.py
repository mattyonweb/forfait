from typing import List
from unittest import TestCase
from typing import *

from forfait.astnodes import AstNode
from forfait.optimizer import Optimizer, stdlib_peeps
from forfait.parser.firstphase import FirstPhase
from forfait.stdlibs.basic_stdlib import STDLIB


class TestOptimizer(TestCase):
    def sequence_tester(self, source, expected: list):
        seq: Sequence = FirstPhase(STDLIB).parse_and_typecheck(source)[0]
        opt = Optimizer(STDLIB, stdlib_peeps).optimization_round(seq.funcs)

        self.assertListEqual(
            expected,
            [x.funcname for x in opt]
        )

    def whole_program_tester(self, source, expected: str):
        nodes: list[AstNode] = FirstPhase(STDLIB).parse_and_typecheck(source)
        opt: list[AstNode]   = Optimizer(STDLIB, stdlib_peeps).optimize(nodes)

        self.assertEqual(
            expected.strip(),
            " ".join([str(x) for x in opt]).strip()
        )

    #######################################################

    def test_optimize_double_swap(self):
        self.sequence_tester(
            "1 3 swap swap 5",
            ["1", "3", "5"]
        )

    def test_optimize_double_swap_quoted(self):
        self.whole_program_tester(
            "[| swap swap |]",
            "[|  |] "
        )

    def test_optimize_double_swap_quoted_among_others(self):
        self.whole_program_tester(
            "1 3 [| swap swap |]",
            "1 3 [|  |] "
        )

    #######################################################

    def test_optimize_arithmetic(self):
        self.sequence_tester(
            "1 3 +u8",
            ["4"]
        )

    def test_optimize_chained_arithmetic(self):
        self.whole_program_tester(
            "16 3 5 7 +u8 +u8 -u8",
            "1"
        )

    def test_optimize_chained_arithmetic2(self):
        self.whole_program_tester(
            "16 3 swap swap 5 7 swap swap +u8 +u8 -u8",
            "1"
        )