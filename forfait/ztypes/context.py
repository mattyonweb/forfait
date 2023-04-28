import copy
import logging
# logging.basicConfig(level=logging.DEBUG)

from typing import *
from typing import Dict, Set, Tuple, List

from forfait.data_structures.graph import Graph
from forfait.ztypes.ztypes import ZTGeneric, ZType, ZTFunction, ZTRowGeneric, ZTRow


class Context:
    def __init__(self):
        self.builtin_types: Dict[str, ZTFunction] = dict()
        self.user_types: Dict[str, ZTFunction] = dict()

        self.generic_subs: Dict[ZTGeneric, ZType] = dict()
        self.inner_type: Dict["Funcall", ZTFunction] = dict()

    def reset(self):
        self.clear_generic_subs()
        self.inner_type = dict()
        self.user_types = dict()


    def _ordered_types(self, l: list["Funcall"]) -> list[ZType]:
        """
        only for debug and testing, return types of single funcalls
        :return:
        """
        return [self.inner_type[funcall] for funcall in l]


    ###############################################################


    def clear_generic_subs(self):
        """
        Usually called at the end of typechecking of a Sequence or similar.

        It finalizes the types of the funcalls saved in the Context (i.e. cuts out the
        unnecessary type arguments) and then clears the substitution equations.
        """
        for k,v in self.generic_subs.items():
            for funcall, ftype in self.inner_type.items():
                self.inner_type[funcall] = ftype.substitute_generic(k,v)

        self.generic_subs: Dict[ZTGeneric, ZType] = dict()

    def get_builtin_type(self, funcname: str) -> ZTFunction:
        """
        Gets the type of a builtin function.
        :param funcname: function name
        :return: type of the function
        """
        # deepcopy needed, otherwise you may have the same
        #   identity :: ''S T -> ''S T
        # everywhere in your program, and the type inferences on T would propagate
        # in every occurrence of identity
        return copy.deepcopy(self.builtin_types[funcname])


    def get_userdefined_type(self, funcname: str):
        """
        :param funcname: name of user-defined function
        :return: type
        """
        return copy.deepcopy(self.user_types[funcname])


    def add_generic_sub(self, generic_type: ZTGeneric, new_type: ZType):
        """
        Adds a new substitution equation to the context. It may modify the existing
        substitutions, similarly to Algorithm W.
        :param generic_type:
        :param new_type:
        :return:
        """

        # elision of obvious equation T = T
        if generic_type == new_type:
            return

        # If ''S (a RowGeneric) is going to be sostituted by [''S] (a Row with the same RowGeneric and nothing else)
        # then you are de facto making a trivial substitution ''S = ''S
        if isinstance(generic_type, ZTRowGeneric) and (
                isinstance(new_type, ZTRow) and len(new_type.types)==0 and new_type.row_var==generic_type
        ):
            return

        # if genericvar already in the dict, unify the old substitution with the
        # new; if the types are compatible, the unification will be ok.
        if generic_type in self.generic_subs:
            temp_ctx = Context()
            old = self.generic_subs[generic_type]
            old.unify(new_type, temp_ctx)

            # substitute in the currently known substitutions
            for key, value in temp_ctx.generic_subs.items():
                self.sub_in_subs(key, value)
            for key, value in temp_ctx.generic_subs.items():
                if key not in self.generic_subs:
                    self.generic_subs[key] = value

        else:
            for key, value in self.generic_subs.items():
                self.generic_subs[key] = value.substitute_generic(generic_type, new_type)
            self.generic_subs[generic_type] = new_type


    def sub_in_subs(self, generic: ZTGeneric, new: ZType):
        """
        Apply this substitution to the right-hand side of all the currently stored subs.
        :param generic:
        :param new:
        :return:
        """
        for key, value in self.generic_subs.items():
            self.generic_subs[key] = value.substitute_generic(generic, new)


    def finalize_funcall_types(self):
        """
        When the typechecking phase is over, for some reason that i don't quite understand
        all the `Funcall` types stored in ctx (and in the `Funcall`s too) store the type of the
        stack _at that moment_ instead of the correct type of _that_ Funcall.
        This function solves this problem brutally, by employing the arity of functions.
        """
        for funcall, typedef in self.inner_type.items():
            typedef.left.keep_last_n(funcall.arity_in)
            typedef.right.keep_last_n(funcall.arity_out)

    ##################################################

    def add_userfunction_type(self, funcname: str, t: ZTFunction):
        self.user_types[funcname] = t

    def _find_generics_inside(self, t: ZType) -> Set[ZTGeneric]:
        # just a helper function around ztype.find_generic_inside
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

            for neigh in self._find_generics_inside(sub_type):
                dependency_graph.add_edge(generic, neigh)
                logging.debug(f"From {generic} ~~> {sub_type}: added to graph: {generic} ==> {neigh}")


        return self.generic_subs, dependency_graph.ordered_visit()