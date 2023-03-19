from unittest import TestCase
from typing import *

from forfait.astnodes import AstNode
from forfait.parser import Parser
from forfait.ztypes.context import get_stdlib


class TestParser(TestCase):
    def parse_simple_sequence(self, code: str, expected_type) -> AstNode:
        ctx = get_stdlib()
        sequence = Parser(ctx).parse(code)[0]

        self.assertEqual(
            expected_type,
            str(sequence.typeof(ctx)),
        )

    def test_1(self):
        self.parse_simple_sequence(
            "1 3 5",
            "( -> U8 U8 U8)"
        )

    def test_quotes1(self):
        self.parse_simple_sequence(
            "[| 1 3 5 |]",
            "( -> ( -> U8 U8 U8))"
        )

    def test_quotes2(self):
        self.parse_simple_sequence(
            "0 5 [| dup u16 store-at |] indexed-iter",
            "( -> )"
        )

    def test_quotes3(self):
        self.parse_simple_sequence(
            "[| dup dup |]" ,
            "( -> )"
        )