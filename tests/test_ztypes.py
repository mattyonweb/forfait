from unittest import TestCase
from typing import *

from forfait.my_exceptions import ZException
from forfait.ztypes import *
from forfait.ztypes.context import Context
from forfait.ztypes.ztypes import ZTFunction, ZTBase, ZTGeneric, type_of_application


class TestFunctionApplication_nopoly(TestCase):
    def assert_type(self, f1, f2, expected: str):
        ctx = Context()

        self.assertEqual(
            str(type_of_application(f1, f2, ctx)),
            expected
        )

    def assert_fail(self, f1, f2):
        try:
            ctx = Context()
            result = type_of_application(f1, f2, ctx)
            self.fail("Obtained:\n" + str(result))
        except ZException as e:
            pass

    def test_lr_longer_rl(self):
        f1 = ZTFunction([ZTBase.U8], [ZTBase.U8, ZTBase.U16, ZTBase.BOOL])
        f2 = ZTFunction([ZTBase.BOOL], [ZTBase.S8])
        self.assert_type(f1, f2, "(U8 -> U8 U16 S8)")

    def test_rl_longer_lr(self):
        f1 = ZTFunction([ZTBase.U8], [ZTBase.U16])
        f2 = ZTFunction([ZTBase.BOOL, ZTBase.BOOL, ZTBase.U16], [ZTBase.S8])
        self.assert_type(f1, f2, "(BOOL BOOL U8 -> S8)")

    def test_rl_equal_lr(self):
        f1 = ZTFunction([ZTBase.U8], [ZTBase.U16, ZTBase.S8])
        f2 = ZTFunction([ZTBase.U16, ZTBase.S8], [ZTBase.BOOL])
        self.assert_type(f1, f2, "(U8 -> BOOL)")

    def test_fail(self):
        f1 = ZTFunction([ZTBase.U8], [ZTBase.U16])
        f2 = ZTFunction([ZTBase.S8], [ZTBase.BOOL])
        self.assert_fail(f1, f2)

#################################################################

class TestFunctionApplication_polymorphism(TestCase):
    def assert_type(self, f1, f2, expected: str):
        ctx = Context()

        self.assertEqual(
            expected,
            str(type_of_application(f1, f2, ctx)),
        )

    def assert_fail(self, f1, f2):
        try:
            ctx = Context()
            result = type_of_application(f1, f2, ctx)
            self.fail("Obtained:\n" + str(result))
        except ZException as e:
            pass

    def test_global_poly1(self):
        A = ZTGeneric("A")
        dup  = ZTFunction([A], [A, A])
        add1 = ZTFunction([ZTBase.U8, ZTBase.U8], [ZTBase.U8])
        self.assert_type(dup, add1, "(U8 -> U8)")

    def test_global_poly2_remains_generic(self):
        A = ZTGeneric("A")
        B = ZTGeneric("B")
        X = ZTGeneric("X")
        swap = ZTFunction([A, B], [B, A])
        dup  = ZTFunction([X], [X, X])
        self.assert_type(swap, dup, "('X 'B -> 'B 'X 'X)")

    def test_global_poly3_hof(self):
        A = ZTGeneric("A")
        B = ZTGeneric("B")
        f1 = ZTFunction([ZTFunction([A], [ZTBase.U8]), B, A],
                          [A, B])
        f2 = ZTFunction([ZTBase.U16, ZTBase.BOOL], [ZTBase.S8])
        self.assert_type(f1, f2, "((U16 -> U8) BOOL U16 -> S8)")