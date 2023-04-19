from unittest import TestCase
from typing import *

from forfait.astnodes import AstNode, Funcdef
from forfait.parser.parser import Parser
from forfait.stdlibs.basic_stdlib import get_stdlib


class TestParser(TestCase):
    def parse_simple_sequence(self, code: str, expected_type):
        ctx = get_stdlib()
        sequence = Parser(ctx).parse(code)[0]

        self.assertEqual(
            expected_type,
            str(sequence.typeof(ctx)),
        )

    def typeof_funcdef(self, code: str, expected_type):
        ctx = get_stdlib()
        funcdef: Funcdef = Parser(ctx).parse(code)[0]

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