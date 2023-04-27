import logging
logging.basicConfig(level=logging.DEBUG)

from unittest import TestCase
# from typing import *

from forfait.astnodes import AstNode, Funcdef, Sequence
from forfait.parser.firstphase import FirstPhase
from forfait.stdlibs.basic_stdlib import get_stdlib


class TestParser_FinalType(TestCase):
    def parse_simple_sequence(self, code: str, expected_type):
        ctx = get_stdlib()
        ctx.reset()

        sequence = FirstPhase(ctx).parse_and_typecheck(code)[0]

        self.assertEqual(
            expected_type,
            str(sequence.typeof(ctx)),
        )

    def parse_simple_sequence_and_get_single_types(self, code: str):
        ctx = get_stdlib()
        ctx.reset()

        parser = FirstPhase(ctx)
        sequence = parser.parse_and_typecheck(code)[0]

        assert isinstance(sequence, Sequence)

        return ctx._ordered_types(sequence.funcs)


    def typeof_funcdef(self, code: str, expected_type):
        ctx = get_stdlib()
        funcdef: Funcdef = FirstPhase(ctx).parse_and_typecheck(code)[0]

        self.assertEqual(
            expected_type,
            str(funcdef.typeof(ctx)),
        )

    def test_1(self):
        self.parse_simple_sequence(
            "1 3 5",
            "(''S -> ''S U8 U8 U8)"
        )

    def test_quotes1(self):
        self.parse_simple_sequence(
            "[| 1 3 5 |]",
            "(''NQ -> ''NQ (''S -> ''S U8 U8 U8))"
        )

    def test_quotes2(self):
        self.parse_simple_sequence(
            "0 5 [| dup u16 store-at |] indexed-iter",
            "(''S -> ''S)"
        )

    def test_quotes3(self):
        self.parse_simple_sequence(
            "[| dup dup |]" ,
            "(''NQ -> ''NQ (''S 'T -> ''S 'T 'T 'T))"
        )

    def test_quotes4(self):
        self.parse_simple_sequence(
            "1 10 [| drop |] indexed-iter" ,
            "(''S -> ''S)"
        )

    def test_quotes5(self):
        # "underflow" of the stack inside a quote should work correctly!
        self.parse_simple_sequence(
            "1 10 [| drop |] test" ,
            "(''S -> ''S U8)"
        )

    def test_quotes_while(self):
        self.typeof_funcdef(
            "1 1 [| dup 100 <=u8 |] [| swap over +u8 |] while swap drop" ,
            "(''S -> ''S U8)"
        )

    # def test_recursive(self):
    #     self.typeof_funcdef(
    #         ": foo 1 +u8 foo ;" ,
    #         "(''S -> ''S)"
    #     )

#######################################################

class TestParser_SingleFunctions(TestCase):

    def parse_simple_sequence_and_get_single_types(self, code: str):
        ctx = get_stdlib()
        ctx.reset()

        parser = FirstPhase(ctx)
        sequence = parser.parse_and_typecheck(code)[0]

        assert isinstance(sequence, Sequence)

        return ctx._ordered_types(sequence.funcs)

    def my_assert(self, l: list["ZType"], idx: int, expected: str):
        self.assertEqual(
            str(l[idx]),
            expected
        )

    ###############################

    def test_double_identity_different_types(self):
        l = self.parse_simple_sequence_and_get_single_types(
            "3 identity 5 u16 identity"
        )

        self.my_assert(l, 1,
            "(''S U8 -> ''S U8)"
        )
        self.my_assert(l, 4,
            "(''S U16 -> ''S U16)"
        )

    def test_double_identity_different_types_quotations(self):
        l = self.parse_simple_sequence_and_get_single_types(
            "3 identity [| 1 2 3 |] identity"
        )

        self.my_assert(l, 1,
            "(''S U8 -> ''S U8)"
        )
        self.my_assert(l, 3,
            "(''S (''S -> ''S U8 U8 U8) -> ''S (''S -> ''S U8 U8 U8))"
        )

    def test_long_distance_effect(self):
        l = self.parse_simple_sequence_and_get_single_types(
            "swap 3 u16 +u16 [| 1 2 3 |] drop drop >=u8"
        )

        self.my_assert(l, 0,
            "(''S U16 U8 -> ''S U8 U16)"
        )
