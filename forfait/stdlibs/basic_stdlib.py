from typing import *

from forfait.ztypes.context import Context
from forfait.ztypes.ztypes import *


def get_stdlib():
    import copy
    return copy.deepcopy(STDLIB)

# CONVENTIONS:
#  - First TRowGeneric shall be called ''S, the second ''R, the other boh
#  - First TGeneric shall be called 'T, second 'U, third 'V, ecc
STDLIB = Context()

T = ZTGeneric("T")
S = ZTRowGeneric("S")
dup = ZTFunc(S, [T], [T, T])
STDLIB.builtin_types["dup"] = dup

T = ZTGeneric("T")
S = ZTRowGeneric("S")
drop = ZTFunc(S, [T], [])
STDLIB.builtin_types["drop"] = drop

T = ZTGeneric("T")
U = ZTGeneric("U")
S = ZTRowGeneric("S")
swap = ZTFunc(S, [T, U], [U, T])
STDLIB.builtin_types["swap"] = swap

T = ZTGeneric("T")
U = ZTGeneric("U")
S = ZTRowGeneric("S")
over = ZTFunc(S, [T, U], [T, U, T])
STDLIB.builtin_types["over"] = over


S = ZTRowGeneric("S")
inc_8bit = ZTFunc(S, [ZTBase.U8], [ZTBase.U8])
STDLIB.builtin_types["inc-8bit"] = inc_8bit

S = ZTRowGeneric("S")
dec_8bit = ZTFunc(S, [ZTBase.U8], [ZTBase.U8])
STDLIB.builtin_types["dec-8bit"] = dec_8bit

S = ZTRowGeneric("S")
inc_16bit = ZTFunc(S, [ZTBase.U16], [ZTBase.U16])
STDLIB.builtin_types["inc-16bit"] = inc_16bit

S = ZTRowGeneric("S")
dec_16bit = ZTFunc(S, [ZTBase.U16], [ZTBase.U16])
STDLIB.builtin_types["dec-16bit"] = dec_16bit

# control flow
T = ZTGeneric("T")
S = ZTRowGeneric("S")
if_ = ZTFunc(S, [T, T, ZTBase.BOOL], [T])
STDLIB.builtin_types["if"] = if_

# loops
S = ZTRowGeneric("S")
R = ZTRowGeneric("R")
indexed_iter_8bit = ZTFunc(S, [ZTBase.U8, ZTBase.U8, ZTFunc(R, [ZTBase.U8], [])], [])
STDLIB.builtin_types["indexed-iter"] = indexed_iter_8bit

# while (fa schifo)
S = ZTRowGeneric("S")
R = ZTRowGeneric("R")
while_loop = ZTFunc(S, [ZTFunc(R, [], [ZTBase.BOOL])], [])
STDLIB.builtin_types["while"] = while_loop

# 8bit arithmetic operations
S = ZTRowGeneric("S")
add_8bit = ZTFunc(S, [ZTBase.U8, ZTBase.U8], [ZTBase.U8])
STDLIB.builtin_types["+u8"] = add_8bit

S = ZTRowGeneric("S")
sub_8bit = ZTFunc(S, [ZTBase.U8, ZTBase.U8], [ZTBase.U8])
STDLIB.builtin_types["-u8"] = sub_8bit

S = ZTRowGeneric("S")
mult_8bit = ZTFunc(S, [ZTBase.U8, ZTBase.U8], [ZTBase.U8])
STDLIB.builtin_types["*u8"] = mult_8bit

S = ZTRowGeneric("S")
div_8bit = ZTFunc(S, [ZTBase.U8, ZTBase.U8], [ZTBase.U8])
STDLIB.builtin_types["/u8"] = div_8bit

# comparisonsctx.clear_generic_subs()
STDLIB.builtin_types[">u8"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8, ZTBase.U8], [ZTBase.BOOL])
STDLIB.builtin_types["<u8"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8, ZTBase.U8], [ZTBase.BOOL])
STDLIB.builtin_types[">=u8"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8, ZTBase.U8], [ZTBase.BOOL])
STDLIB.builtin_types["<=u8"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8, ZTBase.U8], [ZTBase.BOOL])
STDLIB.builtin_types["==u8"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8, ZTBase.U8], [ZTBase.BOOL])
STDLIB.builtin_types["!=u8"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8, ZTBase.U8], [ZTBase.BOOL])

# converters
STDLIB.builtin_types["u16"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8], [ZTBase.U16])

# store-to-memory
T = ZTGeneric("T")
store = ZTFunc(ZTRowGeneric("S"), [T, ZTBase.U16], [])
STDLIB.builtin_types["store-at"] = store

# eval quotation
S = ZTRowGeneric("S")
R = ZTRowGeneric("R")
STDLIB.builtin_types["eval"] = ZTFuncHelper(
    S, [ZTFuncHelper(S, [], R, [])],
    R, []
)

# show stack (removable?)
S = ZTRowGeneric("S")
STDLIB.builtin_types[":s"] = ZTFuncHelper(
    S, [],
    S, []
)

# clear stack (?)
S = ZTRowGeneric("S")
R = ZTRowGeneric("R")
STDLIB.builtin_types["__clear"] = ZTFuncHelper(
    S, [],
    R, []
)