from abc import abstractmethod
from enum import Enum
from typing import *

import logging as log

from forfait.my_exceptions import ZException

class ZTypeError(ZException):
    def __init__(self, explanation: str, *args: object) -> None:
        super().__init__(
            explanation,
            *args[1:]
        )

class UnificationError(ZTypeError):
    def __init__(self, t1: "ZType", t2: "ZType", ctx: "Context", *args: object) -> None:
        super().__init__(
            f"Can't unify:\n\t{t1}\nwith:\n\t{t2}\n\nContext is:\n{ctx}",
            *args[1:]
        )

##################################################

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

##################################################

class ZTComposite(ZType):
    def __init__(self, typename: str, inner_types: list[ZType]):
        self.typename = typename
        self.inner_types = inner_types

        if len(self.inner_types) == 0:
            raise ZTypeError(self, "It is not a composite type with 0 inner types!")

    def unify(self, other: "ZType", ctx: "Context"):
        if isinstance(other, ZTGeneric):
            other.unify(self, ctx)

        if isinstance(other, ZTComposite):
            if len(self.inner_types) != len(other.inner_types):
                raise UnificationError(self, other, "Can't unify composite types as they have different arities")
            if self.typename != other.typename:
                raise UnificationError(self, other, "Can't unify two different composite types")

            for l, r in zip(self.inner_types, other.inner_types):
                l.unify(r, ctx)
            return

        raise UnificationError(self, other, "Can't unify a composite type with non-generic non-composite type")


    def substitute_generic(self, gen: "ZTGeneric", new: "ZType") -> "ZType":
        """
        Exchanges any generic type contained within self (if any) with a concrete type instances
        """
        self.inner_types = [new if gen == t else t for t in self.inner_types]
        return self


    def find_generics_inside(self, s: Set["ZTGeneric"]):
        """
        Find any generic nested inside a type and put them in a set
        """
        for t in self.inner_types:
            if isinstance(t, ZTGeneric):
                s.add(t)

    def __str__(self):
        return f"{self.typename}<{' '.join(str(t) for t in self.inner_types).strip()}>"

def ZTList(t: ZType):
    return ZTComposite("LIST", [t])
def ZTMaybe(t: ZType):
    return ZTComposite("MAYBE", [t])

##################################################

class ZTGeneric(ZType):
    counter = 0

    def __init__(self, human_name: str):
        self.human_name = human_name
        self.counter = ZTGeneric.counter
        ZTGeneric.counter += 1

    def unify(self, other: ZType, ctx: "Context"):
        log.debug(f"New unify equality: {self} =?= {other}")
        ctx.add_generic_sub(self, other)

    def find_generics_inside(self, s: Set["ZTGeneric"]):
        s.add(self)

    def __str__(self):
        return f"'{self.human_name}"

##################################################

class ZTRowGeneric(ZTGeneric):
    counter = 0

    def __init__(self, human_name: str):
        self.human_name = human_name
        self.counter = ZTRowGeneric.counter
        ZTRowGeneric.counter += 1

    def unify(self, other: ZType, ctx: "Context"):
        log.debug(f"New unify equality: {self} =?= {other}")
        ctx.add_generic_sub(self, other)

    def find_generics_inside(self, s: Set["ZTGeneric"]):
        s.add(self)

    def __str__(self):
        # return f"''{self.human_name}_{self.counter}"
        return f"''{self.human_name}"

##################################################

class ZTRow(ZType):
    def __init__(self, row_var: ZTRowGeneric, types: List[ZType]):
        self.row_var = row_var
        self.types = types

    def size(self):
        return len(self.types)

    def unify(self, other: "ZType", ctx: "Context"):
        if isinstance(other, ZTGeneric):
            other.unify(self, ctx)

        if isinstance(other, ZTRow):
            self_len, other_len = len(self.types), len(other.types)

            for i in range(min(self_len, other_len)):
                self.types[-(i + 1)].unify(self.types[-(i + 1)], ctx)

            if self_len <= other_len:
                self.row_var.unify(ZTRow(other.row_var, other.types[:other_len - self_len]), ctx)
            else:
                other.row_var.unify(ZTRow(self.row_var, self.types[:self_len - other_len]), ctx)


    def find_generics_inside(self, s: Set["ZTGeneric"]):
        for t in self.types:
            t.find_generics_inside(s)
        s.add(self.row_var)

    def substitute_generic(self, gen: "ZTGeneric", new: "ZType") -> "ZType":
        for i, t in enumerate(self.types):
            if t == gen:
                self.types[i] = new

        if self.row_var == gen:
            if isinstance(new, ZTRow):
                self.row_var = new.row_var
                self.types   = new.types + self.types
            elif isinstance(new, ZTRowGeneric):
                self.row_var = new
            else:
                print("oh no")
                breakpoint()


        return self
    
    def __str__(self):
        return (str(self.row_var).strip() + " " + " ".join([str(t) for t in self.types]).strip()).strip()

##########################################################

# helper functions
def ZTFunc(stackgeneric, left, right):
    return ZTFunction(ZTRow(stackgeneric, left), ZTRow(stackgeneric, right))
def ZTFuncHelper(genrowvar1, left, genrowvar2, right):
    return ZTFunction(ZTRow(genrowvar1, left), ZTRow(genrowvar2, right))


class ZTFunction(ZType):
    def __init__(self, left: ZTRow, right: ZTRow):
        self.left  = left
        self.right = right

    def unify(self, other: ZType, ctx: "Context"):
        if isinstance(other, ZTGeneric):
            return other.unify(self, ctx)

        if not isinstance(other, ZTFunction):
            raise UnificationError(self, other, ctx)

        # Per la left-side della funzione, matcho prima tutti i tipi concreti possibili
        # Es:
        #    foo :: 'S u8 u8 T  bool -> ...
        #    bar :: 'R    u8 u8 bool -> ...
        #                 ^^^^^^^^^^  u8=u8, T=u8, bool=bool
        # e poi, nel caso di lunghezze diverse dello stack, matcho i rimanenti tipi concreti + stackgeneric con lo stack
        # generic del tipo con meno tipi concreti
        # Es:
        #    foo :: 'S u8 u8 T  bool -> ...
        #            | /
        #    bar :: 'R    u8 u8 bool -> ...
        #           ^^^ 'R = 'S u8
        #
        self_len, other_len = len(self.left.types), len(other.left.types)

        for i in range(min(self_len, other_len)):
            self.left.types[-(i+1)].unify(other.left.types[-(i+1)], ctx)

        if self_len <= other_len:
            self.left.row_var.unify(ZTRow(other.left.row_var, other.left.types[:other_len - self_len]), ctx)
        else:
            other.left.row_var.unify(ZTRow(self.left.row_var, self.left.types[:self_len - other_len]), ctx)


        # idem per right side
        self_len, other_len = len(self.right.types), len(other.right.types)

        for i in range(min(self_len, other_len)):
            self.right.types[-(i+1)].unify(other.right.types[-(i+1)], ctx)

        if self_len <= other_len:
            self.right.row_var.unify(ZTRow(other.right.row_var, other.right.types[:other_len - self_len]), ctx)
        else:
            other.right.row_var.unify(ZTRow(self.right.row_var, self.right.types[:self_len - other_len]), ctx)


        
    def find_generics_inside(self, s: Set["ZTGeneric"]):
        for l in self.left.types:
            l.find_generics_inside(s)
        for r in self.right.types:
            r.find_generics_inside(s)


    def substitute_generic(self, generic: ZTGeneric, t: ZType):
        # Recursively visit left and right, looking for generics
        for i, l in enumerate(self.left.types):
            if l == generic:
                self.left.types[i] = t
            else:
                self.left.types[i] = self.left.types[i].substitute_generic(generic, t)

        for i, r in enumerate(self.right.types):
            if r == generic:
                self.right.types[i] = t
            else:
                self.right.types[i] = self.right.types[i].substitute_generic(generic, t)

        if self.left.row_var == generic:
            if isinstance(t, ZTRow):
                self.left.row_var = t.row_var
                self.left.types = t.types + self.left.types
            elif isinstance(t, ZTRowGeneric):
                self.left.row_var = t
            else:
                print("Non so cosa vuol dire questo")
                breakpoint()

        if self.right.row_var == generic:
            if isinstance(t, ZTRow):
                self.right.row_var = t.row_var
                self.right.types = t.types + self.right.types
            elif isinstance(t, ZTRowGeneric):
                self.right.row_var = t
            else:
                print("Non so cosa vuol dire questo")
                breakpoint()

        return self

    def __str__(self):
        return f"({self.left} -> {self.right})"

#########################################

def takelasts(l, n) -> list:
    if len(l) < n:
        return l # ??
    if len(l) == n:
        return l
    return l[-n:]


def type_of_application_rowpoly(t1: ZTFunction, t2: ZTFunction, ctx: "Context") -> ZTFunction:
    assert isinstance(t1, ZTFunction)  # assumi che il primo elemento di ogni lista sia un TRowGeneric
    assert isinstance(t2, ZTFunction)

    ctx.clear_generic_subs()

    ll, lr = t1.left, t1.right
    rl, rr = t2.left, t2.right

    if lr.size() > rl.size():
        common_seq_len = rl.size()
        for tl, tr in zip(takelasts(lr.types, common_seq_len), rl.types):
            tl.unify(tr, ctx)

        # unifico la stack variable con il resto della lista di tipi
        rl.row_var.unify(
            ZTRow(lr.row_var, lr.types if common_seq_len == 0 else lr.types[:-common_seq_len]),
            ctx
        )

        candidate = ZTFunction(ll, rr)

    elif lr.size() < rl.size():
        common_seq_len = lr.size()
        for tl, tr in zip(lr.types, takelasts(rl.types, common_seq_len)):
            tl.unify(tr, ctx)

        # unifico la stack variable con il resto della lista di tipi
        lr.row_var.unify(
            ZTRow(rl.row_var, rl.types if common_seq_len == 0 else rl.types[:-common_seq_len]),
            ctx
        )
        candidate = ZTFunction(ll, rr)

    else:
        for tl, tr in zip(lr.types, rl.types):
            tl.unify(tr, ctx)
        lr.row_var.unify(rl.row_var, ctx)
        candidate = ZTFunction(ll, rr)

    # performs ordered rewriting of `Generic`s in an order given by the dependency graph
    subs, order = ctx.ordered_subs()
    for k in order:
        if k not in subs:  # HACK: TODO: da ripensare eh
            continue
        candidate.substitute_generic(k, subs[k])

        ## these are so that intermediate functions with generic types assume a concrete value whenever possible
        ## NB: not so sure this makes sens
        ll.substitute_generic(k, subs[k])
        lr.substitute_generic(k, subs[k])
        rl.substitute_generic(k, subs[k])
        rr.substitute_generic(k, subs[k])
    return candidate