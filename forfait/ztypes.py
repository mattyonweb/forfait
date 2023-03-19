from abc import abstractmethod
from enum import Enum
from typing import *

from forfait.data_structures.graph import Graph
from forfait.my_exceptions import ZException


class UnificationError(ZException):
    def __init__(self, t1: "ZType", t2: "ZType", ctx: "Context", *args: object) -> None:
        super().__init__(
            f"Can't unify:\n\t{t1}\nwith:\n\t{t2}\n\nContext is:\n{ctx}",
            *args[1:]
        )


class ZType:
    @abstractmethod
    def unify(self, other: "ZType", ctx: "Context"):
        pass

    def substitute_generic(self, gen: "ZTGeneric", new: "ZType") -> "ZType":
        """
        Exchanges any generic type contained within self (if any) with a concrete type instances
        """
        return self

    def find_generics_inside(self, s: Set["ZTGeneric"]):
        """
        Find any generic nested inside a type and put them in a set
        """
        pass

##################################################

class ZTBase(ZType, Enum):
    U8 = 1
    S8 = 2
    U16 = 3
    BOOL = 4

    def unify(self, other: "ZType", ctx: "Context"):
        if isinstance(other, ZTGeneric):
            return other.unify(self, ctx)

        if not isinstance(other, ZTBase):
            raise UnificationError(self, other, ctx)

        if self.value != other.value:
            raise UnificationError(self, other, ctx)

    def __str__(self):
        return self.name


class ZTGeneric(ZType):
    def __init__(self, human_name: str):
        self.human_name = human_name

    def unify(self, other: ZType, ctx: "Context"):
        ctx.add_generic_sub(self, other)

    def find_generics_inside(self, s: Set["ZTGeneric"]):
        s.add(self)

    def __str__(self):
        return f"'{self.human_name}"



class ZTFunction(ZType):
    def __init__(self, left: List[ZType], right: List[ZType]):
        self.left  = left
        self.right = right

    def unify(self, other: ZType, ctx: "Context"):
        if isinstance(other, ZTGeneric):
            return other.unify(self, ctx)

        if not isinstance(other, ZTFunction):
            raise UnificationError(self, other, ctx)

        for (l1, l2) in zip(self.left, other.left):
            l1.unify(l2, ctx)
        for (r1, r2) in zip(self.right, other.right):
            r1.unify(r2, ctx)

    def find_generics_inside(self, s: Set["ZTGeneric"]):
        for l in self.left:
            l.find_generics_inside(s)
        for r in self.right:
            r.find_generics_inside(s)


    def substitute_generic(self, generic: ZTGeneric, t: ZType):
        # Recursively visit left and right, looking for generics
        for i, l in enumerate(self.left):
            if l == generic:
                self.left[i] = t
            else:
                self.left[i] = self.left[i].substitute_generic(generic, t)

        for i, r in enumerate(self.right):
            if r == generic:
                self.right[i] = t
            else:
                self.right[i] = self.right[i].substitute_generic(generic, t)

        return self

    def __str__(self):
        stack_left  = " ".join([str(s) for s in self.left]).strip()
        stack_right = " ".join([str(s) for s in self.right]).strip()
        return f"({stack_left} -> {stack_right})"

"""
swap dup +1u8 drop

(A B -> B A)  (X -> X X)  (u8 -> u8)  (C -> )

Idee:
- nel ctx creare una hashmap  { GenericTypeVar ==> Optional[ZType] } dove salvare i tipi concreti
- In una prima fase fai unification due a due, e riempi la hasmap
- In una seconda fase, rivisiti l'AST applicando le sostituzioni descritte nella hasmap
"""

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



#########################################

def type_of_application(t1: ZTFunction, t2: ZTFunction, ctx: Context) -> ZTFunction:
    """
    Returns the type
    """
    assert isinstance(t1, ZTFunction)
    assert isinstance(t2, ZTFunction)

    ll, lr = t1.left, t1.right
    rl, rr = t2.left, t2.right

    if len(lr) > len(rl):
        common_seq_len = len(rl)
        for tl, tr in zip(lr[-common_seq_len:], rl):
            tl.unify(tr, ctx)
        candidate = ZTFunction(ll, lr[:-common_seq_len] + rr)

    elif len(lr) < len(rl):
        common_seq_len = len(lr)
        for tl, tr in zip(lr, rl[-common_seq_len:]):
            tl.unify(tr, ctx)
        candidate = ZTFunction(rl[:-common_seq_len] + ll, rr)

    else:
        for tl, tr in zip(lr, rl):
            tl.unify(tr, ctx)
        candidate = ZTFunction(ll, rr)

    subs, order = ctx.ordered_subs()
    for k in order:
        if k not in subs:  # HACK: TODO: da ripensare eh
            continue
        candidate.substitute_generic(k, subs[k])
    return candidate