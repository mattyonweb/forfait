import logging
# logging.basicConfig(level=logging.DEBUG)

from typing import *
from typing import Dict, Set, Tuple, List

from forfait.data_structures.graph import Graph
from forfait.ztypes.ztypes import ZTGeneric, ZType, ZTFunction


class Context:
    def __init__(self):
        self.generic_subs: Dict[ZTGeneric, ZType] = dict()
        self.builtin_types: Dict[str, ZTFunction] = dict()
        self.user_types: Dict[str, ZTFunction] = dict()

        self.inner_type: Dict["Funcall", ZTFunction] = dict()

    def reset(self):
        self.clear_generic_subs()
        self.inner_type = dict()
        self.user_types = dict()


    def _ordered_types(self, l: list["Funcall"]) -> list[ZType]:
        """
        only debug, returns types of single funcalls
        :return:
        """
        return [self.inner_type[funcall] for funcall in l]

    ###############################################################

    def clear_generic_subs(self):
        for k,v in self.generic_subs.items():
            for funcall, ftype in self.inner_type.items():
                self.inner_type[funcall] = ftype.substitute_generic(k,v)

        self.generic_subs: Dict[ZTGeneric, ZType] = dict()

    def get_builtin_type(self, funcname):
        import copy
        return copy.deepcopy(self.builtin_types[funcname])

    def get_userdefined_type(self, funcname):
        import copy
        return copy.deepcopy(self.user_types[funcname])

    def add_generic_sub(self, generic_type: ZTGeneric, new_type: ZType):
        if generic_type == new_type:
            return # elision of obvious equation T = T

        if generic_type in self.generic_subs:
            old = self.generic_subs[generic_type]

            temp_ctx = Context()
            old.unify(new_type, temp_ctx)
            for key, value in temp_ctx.generic_subs.items():
                self.sub_in_subs(key, value)

        else:
            for key, value in self.generic_subs.items():
                self.generic_subs[key] = value.substitute_generic(generic_type, new_type)
            self.generic_subs[generic_type] = new_type

    def add_userfunction_type(self, funcname: str, t: ZTFunction):
        self.user_types[funcname] = t

    def __find_generics_inside(self, t: ZType) -> Set[ZTGeneric]:
        generics_inside = set()
        t.find_generics_inside(generics_inside)
        return generics_inside

    def sub_in_subs(self, generic: ZTGeneric, new: ZType):
        for key, value in self.generic_subs.items():
            self.generic_subs[key] = value.substitute_generic(generic, new)

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
                logging.debug(f"From {generic} ~~> {sub_type}: added to graph: {generic} ==> {neigh}")


        return self.generic_subs, dependency_graph.ordered_visit()




##################################################