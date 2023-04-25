## CONVENTIONS:
##  - First TRowGeneric shall be called ''S, the second ''R, the other boh
##  - First TGeneric shall be called 'T, second 'U, third 'V, ecc

from forfait.ztypes.context import Context
from forfait.ztypes.ztypes import *

def get_stdlib():
    import copy
    return copy.deepcopy(STDLIB)

##############################################################

STDLIB = Context()

############## STACK MANIPULATION ##############

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
A, B, C = ZTGeneric("A"), ZTGeneric("B"), ZTGeneric("C")
rotplus = ZTFunc(S, [A, B, C], [C, A, B])
STDLIB.builtin_types["rot+"] = rotplus

S = ZTRowGeneric("S")
A, B, C = ZTGeneric("A"), ZTGeneric("B"), ZTGeneric("C")
rotminus = ZTFunc(S, [A, B, C], [B, C, A])
STDLIB.builtin_types["rot-"] = rotminus



############## FLOW ALTERATIONS ##############

# if
T = ZTGeneric("T")
S = ZTRowGeneric("S")
if_ = ZTFunc(S, [T, T, ZTBase.BOOL], [T])
STDLIB.builtin_types["if"] = if_

# analogo di:  for i in range(start, end): foo(i)
S = ZTRowGeneric("S")
R = ZTRowGeneric("R")
indexed_iter_8bit = ZTFunc(S, [ZTBase.U8, ZTBase.U8, ZTFunc(R, [ZTBase.U8], [])], [])
STDLIB.builtin_types["indexed-iter"] = indexed_iter_8bit

# invariant while (doesn't change stack type at any iteration)
S = ZTRowGeneric("S")
while_loop = ZTFunc(
    S, [ZTFunc(S, [], [ZTBase.BOOL]),
        ZTFunc(S, [], [])],
    []
)
STDLIB.builtin_types["while"] = while_loop



############## ARITHMETIC ##############

S = ZTRowGeneric("S")
inc_8bit = ZTFunc(S, [ZTBase.U8], [ZTBase.U8])
STDLIB.builtin_types["++u8"] = inc_8bit

S = ZTRowGeneric("S")
dec_8bit = ZTFunc(S, [ZTBase.U8], [ZTBase.U8])
STDLIB.builtin_types["--u8"] = dec_8bit

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

###### 16bit 

S = ZTRowGeneric("S")
inc_16bit = ZTFunc(S, [ZTBase.U16], [ZTBase.U16])
STDLIB.builtin_types["++u16"] = inc_16bit

S = ZTRowGeneric("S")
dec_16bit = ZTFunc(S, [ZTBase.U16], [ZTBase.U16])
STDLIB.builtin_types["--u16"] = dec_16bit

# 16bit arithmetic operations
S = ZTRowGeneric("S")
add_16bit = ZTFunc(S, [ZTBase.U16, ZTBase.U16], [ZTBase.U16])
STDLIB.builtin_types["+u16"] = add_16bit

S = ZTRowGeneric("S")
sub_16bit = ZTFunc(S, [ZTBase.U16, ZTBase.U16], [ZTBase.U16])
STDLIB.builtin_types["-u16"] = sub_16bit

S = ZTRowGeneric("S")
mult_16bit = ZTFunc(S, [ZTBase.U16, ZTBase.U16], [ZTBase.U16])
STDLIB.builtin_types["*u16"] = mult_16bit

S = ZTRowGeneric("S")
div_16bit = ZTFunc(S, [ZTBase.U16, ZTBase.U16], [ZTBase.U16])
STDLIB.builtin_types["/u16"] = div_16bit

############## ARITHMETIC COMPARISONS ##############

STDLIB.builtin_types[">u8"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8, ZTBase.U8], [ZTBase.BOOL])
STDLIB.builtin_types["<u8"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8, ZTBase.U8], [ZTBase.BOOL])
STDLIB.builtin_types[">=u8"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8, ZTBase.U8], [ZTBase.BOOL])
STDLIB.builtin_types["<=u8"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8, ZTBase.U8], [ZTBase.BOOL])
STDLIB.builtin_types["==u8"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8, ZTBase.U8], [ZTBase.BOOL])
STDLIB.builtin_types["!=u8"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8, ZTBase.U8], [ZTBase.BOOL])


############## LIST MANIPULATION ##############

T = ZTGeneric("T")
emptylist = ZTFunc(ZTRowGeneric("S"), [], [ZTList(T)])
STDLIB.builtin_types["empty-list"] = emptylist

T = ZTGeneric("T")
L = ZTList(T)
emptylist = ZTFunc(ZTRowGeneric("S"), [L, T], [L])
STDLIB.builtin_types["add-to-list"] = emptylist

T = ZTGeneric("T")
L = ZTList(T)
emptylist = ZTFunc(ZTRowGeneric("S"), [L, T], [L])
STDLIB.builtin_types["last-of-list"] = emptylist

############## CASTS ##############

STDLIB.builtin_types["u16"] = ZTFunc(ZTRowGeneric("S"), [ZTBase.U8], [ZTBase.U16])

############## MEMORY ACCESS ##############

# store-to-memory
T = ZTGeneric("T")
store = ZTFunc(ZTRowGeneric("S"), [T, ZTBase.U16], [])
STDLIB.builtin_types["store-at"] = store

# retrieve
T = ZTGeneric("T")
retrieve = ZTFunc(ZTRowGeneric("S"), [ZTBase.U16], [T])
STDLIB.builtin_types["retrieve-from"] = retrieve

############## HIGHER ORDER FUNCTIONS ##############

# eval quotation
S = ZTRowGeneric("S")
R = ZTRowGeneric("R")
STDLIB.builtin_types["eval"] = ZTFuncHelper(
    S, [ZTFuncHelper(S, [], R, [])],
    R, []
)



############## MISC ##############

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


S = ZTRowGeneric("S")
T = ZTGeneric("T")
STDLIB.builtin_types["identity"] = ZTFuncHelper(
    S, [T],
    S, [T]
)
