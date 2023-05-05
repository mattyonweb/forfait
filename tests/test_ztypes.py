from unittest import TestCase
from typing import *

from forfait.my_exceptions import ZException
from forfait.ztypes import *
from forfait.ztypes.context import Context
from forfait.ztypes.ztypes import ZTFunction, ZTBase, ZTGeneric, type_of_application_rowpoly, ZTFuncHelper, \
    ZTRowGeneric, ZTList, ZTypeError, ZTMaybe

import logging
logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s]:%(message)s")


class TestFunctionApplication_nopoly(TestCase):
    def assert_type(self, f1, f2, expected: str):
        ctx = Context()

        self.assertEqual(
            str(type_of_application_rowpoly(f1, f2, ctx)),
            expected
        )

    def assert_fail(self, f1, f2):
        try:
            ctx = Context()
            result = type_of_application_rowpoly(f1, f2, ctx)
            self.fail("Obtained:\n" + str(result))
        except ZTypeError as e:
            pass

    def test_lr_longer_rl(self):
        T = ZTRowGeneric("T")
        f1 = ZTFuncHelper(T, [ZTBase.U8], T, [ZTBase.U8, ZTBase.U16, ZTBase.BOOL])

        A = ZTRowGeneric("A")
        f2 = ZTFuncHelper(A, [ZTBase.BOOL], A, [ZTBase.S8])

        self.assert_type(f1, f2, "(''T U8 -> ''T U8 U16 S8)")

    def test_rl_longer_lr(self):
        A = ZTRowGeneric("A")
        f1 = ZTFuncHelper(A, [ZTBase.U8], A, [ZTBase.U16])

        T = ZTRowGeneric("T")
        f2 = ZTFuncHelper(T, [ZTBase.BOOL, ZTBase.BOOL, ZTBase.U16], T, [ZTBase.S8])

        self.assert_type(f1, f2, "(''T BOOL BOOL U8 -> ''T S8)")

    def test_rl_equal_lr(self):
        T = ZTRowGeneric("T")
        A = ZTRowGeneric("A")
        f1 = ZTFuncHelper(T, [ZTBase.U8], T, [ZTBase.U16, ZTBase.S8])
        f2 = ZTFuncHelper(A, [ZTBase.U16, ZTBase.S8], A, [ZTBase.BOOL])
        self.assert_type(f1, f2, "(''A U8 -> ''A BOOL)")

    def test_two_consecutive_numbers(self):
        T = ZTRowGeneric("T")
        A = ZTRowGeneric("A")
        f1 = ZTFuncHelper(A, [], A, [ZTBase.U8])
        f2 = ZTFuncHelper(T, [], T, [ZTBase.U8])
        self.assert_type(f1, f2, "(''A -> ''A U8 U8)")

    def test_fail(self):
        T = ZTRowGeneric("T")
        A = ZTRowGeneric("A")
        f1 = ZTFuncHelper(T, [ZTBase.U8], T, [ZTBase.U16])
        f2 = ZTFuncHelper(A, [ZTBase.S8], A, [ZTBase.BOOL])
        self.assert_fail(f1, f2)

#################################################################

class TestFunctionApplication_polymorphism(TestCase):
    def assert_type(self, f1, f2, expected: str):
        ctx = Context()

        self.assertEqual(
            expected,
            str(type_of_application_rowpoly(f1, f2, ctx)),
        )

    def assert_fail(self, f1, f2):
        try:
            ctx = Context()
            result = type_of_application_rowpoly(f1, f2, ctx)
            self.fail("Obtained:\n" + str(result))
        except ZException as e:
            pass

    def test_global_poly1(self):
        T1 = ZTRowGeneric("T1")
        T2 = ZTRowGeneric("T2")

        A = ZTGeneric("A")
        dup  = ZTFuncHelper(T1, [A], T1, [A, A])
        add1 = ZTFuncHelper(T2, [ZTBase.U8, ZTBase.U8], T2, [ZTBase.U8])
        self.assert_type(dup, add1, "(''T2 U8 -> ''T2 U8)")

    def test_global_poly2_remains_generic(self):
        T1 = ZTRowGeneric("T1")
        T2 = ZTRowGeneric("T2")

        A = ZTGeneric("A")
        B = ZTGeneric("B")
        X = ZTGeneric("X")
        swap = ZTFuncHelper(T1, [A, B], T1, [B, A])
        dup  = ZTFuncHelper(T2, [X], T2, [X, X])
        self.assert_type(swap, dup, "(''T1 'X 'B -> ''T1 'B 'X 'X)")

    def test_global_poly3_hof(self):
        T1 = ZTRowGeneric("T1")
        T2 = ZTRowGeneric("T2")
        T3 = ZTRowGeneric("T3")

        A = ZTGeneric("A")
        B = ZTGeneric("B")
        f1 = ZTFuncHelper(
            T1, [ZTFuncHelper(T2, [A], T2, [ZTBase.U8]), B, A],
            T1, [A, B]
        )
        f2 = ZTFuncHelper(T3, [ZTBase.U16, ZTBase.BOOL], T3, [ZTBase.S8])
        self.assert_type(f1, f2, "(''T3 (''T2 U16 -> ''T2 U8) BOOL U16 -> ''T3 S8)")

    def test_global_quote_eval_nogenerics(self):
        A = ZTRowGeneric("A")
        B = ZTRowGeneric("B")
        R = ZTRowGeneric("R")
        S = ZTRowGeneric("S")

        double_add_quoted = ZTFuncHelper(
            S, [],
            S, [ZTFuncHelper(R, [ZTBase.U8, ZTBase.U8, ZTBase.U8], R, [ZTBase.U8])]
        )
        eval_ = ZTFuncHelper(
            A, [ZTFuncHelper(A, [], B, [])],
            B, []
        )

        self.assert_type(double_add_quoted, eval_, "(''R U8 U8 U8 -> ''R U8)")

    def test_global_poly2_order_of_equation(self):
        S1 = ZTRowGeneric("S")
        S2 = ZTRowGeneric("R")

        A = ZTGeneric("A")
        B = ZTGeneric("B")
        X = ZTGeneric("X")
        swap = ZTFuncHelper(S1, [A], S1, [A])
        dup  = ZTFuncHelper(S2, [X], S2, [B])
        self.assert_type(swap, dup, "(''R 'X -> ''R 'B)")

#################################################################

class TestFunctionApplication_composite_types(TestCase):
    def assert_type(self, f1, f2, expected: str):
        ctx = Context()

        self.assertEqual(
            expected,
            str(type_of_application_rowpoly(f1, f2, ctx)),
        )

    def assert_fail(self, f1, f2):
        try:
            ctx = Context()
            result = type_of_application_rowpoly(f1, f2, ctx)
            self.fail("Obtained:\n" + str(result))
        except ZException as e:
            pass

    def test_comp1(self):
        S = ZTRowGeneric("S")
        R = ZTRowGeneric("R")

        A = ZTGeneric("A")
        list_gen  = ZTList(A)
        list_conc = ZTList(ZTBase.U8)
        list_gen2 = ZTList(A)

        f1 = ZTFuncHelper(S, [A], S, [list_gen])
        f2 = ZTFuncHelper(R, [list_conc], R, [list_gen2])

        self.assert_type(f1, f2, "(''R U8 -> ''R LIST<U8>)")

    def test_same_arity_type_differs_if_names_are_different(self):
        S = ZTRowGeneric("S")
        R = ZTRowGeneric("R")

        A = ZTGeneric("A")
        l  = ZTList(A)
        m = ZTMaybe(ZTBase.U8)

        f1 = ZTFuncHelper(S, [A], S, [l])
        f2 = ZTFuncHelper(R, [m], R, [A])
        self.assert_fail(f1, f2)
