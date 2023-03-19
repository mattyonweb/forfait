from typing import *
from typing import Dict, Set, Tuple, List

from forfait.data_structures.graph import Graph
from forfait.ztypes.ztypes import ZTGeneric, ZType, ZTFunction, ZTBase


class Context:
    def __init__(self):
        self.generic_subs: Dict[ZTGeneric, ZType] = dict()
        self.builtin_types: Dict[str, ZTFunction] = dict()
        self.user_types: Dict[str, ZTFunction] = dict()

    def add_generic_sub(self, generic_type: ZTGeneric, new_type: ZType):
        self.generic_subs[generic_type] = new_type

    def add_userfunction_type(self, funcname: str, t: ZTFunction):
        self.user_types[funcname] = t

    def __find_generics_inside(self, t: ZType) -> Set[ZTGeneric]:
        generics_inside = set()
        t.find_generics_inside(generics_inside)
        return generics_inside

    def ordered_subs(self) -> Tuple[Dict[ZTGeneric, ZType], List[ZTGeneric]]:
        """
        Per effettuare sostituzioni correttamente, l'ordine in cui si effettuano le riscritture
        è importante. Per esempio, se il tipo da riscrivere fosse
            myFoo :: 'a -> 'x
        e il ctx fosse
            'a ~~> ('x -> u8)   [1]
            'x ~~> u16          [2]
        sarebbe sbagliato fare la riscrittura di [2] prima di [1]; otterresti:
            myFoo :: 'a -> u16   e quindi   myFoo :: ('x -> u8) -> u16
        invece del desiderato
            myFoo :: (u16 -> u8) -> u16

        Bisogna quindi analizzare il grafo delle dipendenze fra riscritture. Nel caso sopra il grafo era
            'a  ~~~richiede~~~>  'x
        e semplicemente applichi le riscritture visitando il grado in pre-order (applichi prima
        riscrittura su 'a poi quella su 'x)

        In caso di cicli nel grafo hai un OCCUR FAIL
        """
        dependency_graph = Graph()

        for generic, sub_type in self.generic_subs.items():
            dependency_graph.add_node(generic)

            for neigh in self.__find_generics_inside(sub_type):
                dependency_graph.add_edge(generic, neigh)

        return self.generic_subs, dependency_graph.ordered_visit()

##################################################

STDLIB = Context()

A = ZTGeneric("A")
dup = ZTFunction([A], [A, A])
STDLIB.builtin_types["dup"] = dup

A = ZTGeneric("A")
drop = ZTFunction([A], [])
STDLIB.builtin_types["drop"] = drop

A = ZTGeneric("A")
B = ZTGeneric("B")
swap = ZTFunction([A, B], [B, A])
STDLIB.builtin_types["swap"] = swap

A = ZTGeneric("A")
B = ZTGeneric("B")
over = ZTFunction([A, B], [A, B, A])
STDLIB.builtin_types["over"] = over

T = ZTGeneric("T")
if_ = ZTFunction([ZTBase.BOOL, T, T], [T])
STDLIB.builtin_types["if"] = if_

inc_8bit = ZTFunction([ZTBase.U8], [ZTBase.U8])
STDLIB.builtin_types["inc_8bit"] = inc_8bit

dec_8bit = ZTFunction([ZTBase.U8], [ZTBase.U8])
STDLIB.builtin_types["dec_8bit"] = dec_8bit

inc_16bit = ZTFunction([ZTBase.U16], [ZTBase.U16])
STDLIB.builtin_types["inc_16bit"] = inc_16bit

dec_16bit = ZTFunction([ZTBase.U16], [ZTBase.U16])
STDLIB.builtin_types["dec_16bit"] = dec_16bit

add_8bit = ZTFunction([ZTBase.U8, ZTBase.U8], [ZTBase.U16])
STDLIB.builtin_types["+u8"] = add_8bit