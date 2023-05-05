import copy
import logging
# logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s]:%(message)s")

from typing import *
from typing import Dict, Set, Tuple, List

from forfait.data_structures.graph import Graph
from forfait.utils import Unreachable
from forfait.ztypes.ztypes import ZTGeneric, ZType, ZTFunction, ZTRowGeneric, ZTRow



class Context:
    def __init__(self):
        self.builtin_types: Dict[str, ZTFunction] = dict()
        self.user_types: Dict[str, ZTFunction] = dict()

        self.generic_subs: Dict[int, ZType] = dict()
        self.generic_map: Dict[int, ZTGeneric] = dict()
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
        return [funcall.typeof(None) for funcall in l]


    ###############################################################
    # dealing with generics

    def _store_new_sub(self, generic: ZTGeneric, new: ZType):
        """
        This must be the only way to access self.generic_subs.

        :param generic:
        :param new:
        :return:
        """
        if generic.counter in self.generic_subs:
            if not self.generic_subs[generic.counter].structural_eq(new):
                assert generic.counter not in self.generic_subs
            return
        if generic.counter in self.generic_map:
            if not self.generic_map[generic.counter].structural_eq(generic):
                assert generic.counter not in self.generic_map
            return

        self.generic_subs[generic.counter] = new
        self.generic_map[generic.counter] = generic


    def a_sub_for_generic_already_exists(self, generic: ZTGeneric) -> bool:
        return generic.counter in self.generic_subs


    def rhs_of_sub(self, generic: ZTGeneric) -> ZType:
        """
        Return the right side of the substitution of `generic`.

        :param generic:
        :return:
        """
        if not self.a_sub_for_generic_already_exists(generic):
            raise KeyError(f"{self}\nNo generic named {generic} found in ctx")
        return self.generic_subs[generic.counter]


    def generic_subs_items(self) -> Generator[tuple[ZTGeneric, ZType], None, None]:
        for k, v in self.generic_subs.items():
            yield self.generic_map[k], v


    def clear_generic_subs(self):
        """
        Usually called at the end of typechecking of a Sequence or similar.

        It finalizes the types of the funcalls saved in the Context (i.e. cuts out the
        unnecessary type arguments) and then clears the substitution equations.
        """
        for k,v in self.generic_subs_items():
            for funcall, ftype in self.inner_type.items():
                self.inner_type[funcall] = ftype.substitute_generic(k,v)

        self._clear_all_generic_data()


    def _clear_all_generic_data(self):
        self.generic_subs = dict()
        self.generic_map = dict()


    ####################################################################

    def fresh_type(self, t: ZTFunction) -> ZTFunction:
        t = copy.deepcopy(t)

        for old_generic in self._find_generics_inside(t):
            if isinstance(old_generic, ZTRowGeneric):
                t = t.substitute_generic(old_generic, ZTRowGeneric(old_generic.human_name))
            elif isinstance(old_generic, ZTGeneric):
                t = t.substitute_generic(old_generic, ZTGeneric(old_generic.human_name))
            else:
                raise Unreachable()

        return t


    def fresh_builtin_type(self, funcname: str) -> ZTFunction:
        """
        Gets the type of a builtin function.

        :param funcname: function name
        :return: type of the function
        """
        # deepcopy needed, otherwise you may have the same
        #   identity :: ''S T -> ''S T
        # everywhere in your program, and the type inferences on T would propagate
        # in every occurrence of identity
        t = self.fresh_type(self.builtin_types[funcname])

        logging.debug(f"Generated fresh type signature for builtin {funcname}: {t}")

        return t


    def get_userdefined_type(self, funcname: str):
        """
        :param funcname: name of user-defined function
        :return: type
        """
        # TODO: non va bene. con il passaggio a type.eq() qua dovrai _costruire_ un tipo nuovo
        return copy.deepcopy(self.user_types[funcname])


    def add_generic_sub(self, generic_type: ZTGeneric, new_type: ZType):
        """
        Adds a new substitution equation to the context. It may modify the existing
        substitutions, similarly to Algorithm W.
        :param generic_type:
        :param new_type:
        :return:
        """
        logging.debug(f"Beginning insert in CTX of equation: {generic_type} ~~> {new_type}")

        # elision of obvious equation T = T
        if generic_type.structural_eq(new_type):
            logging.debug(f"  Equation was trivial")
            return

        # elision of obvious equation 'T = 'T or ''S = ''S
        if isinstance(new_type, ZTGeneric) and generic_type.counter == new_type.counter:
            logging.debug(f"  Equation was trivial")
            return

        # If ''S (a RowGeneric) is going to be sostituted by [''S] (a Row with the same RowGeneric and nothing else)
        # then you are de facto making a trivial substitution ''S = ''S
        if isinstance(generic_type, ZTRowGeneric) and (
                isinstance(new_type, ZTRow) and len(new_type.types)==0 and new_type.row_var.counter == generic_type.counter
        ):
            logging.debug(f"  Equation was trivial")
            return

        # occur check
        if generic_type in self._find_generics_inside(new_type):
            raise Exception(
                f"OCCUR CHECK FAIL\n" +
                f"The new candidate substitution:\n" +
                f"\t{generic_type} ~~> {new_type}\n" +
                "fails the occur check."
            )


        # if genericvar already in the dict, unify the old substitution with the
        # new; if the types are compatible, the unification will be ok.
        if self.a_sub_for_generic_already_exists(generic_type):
            logging.debug(f"  Sub with same LHS already in ctx: " +
                          f"{self.generic_subs[generic_type.counter]} ~~> {self.rhs_of_sub(generic_type)}")

            temp_ctx = Context()
            old = self.rhs_of_sub(generic_type) # self.generic_subs[generic_type]
            old.unify(new_type, temp_ctx)

            logging.debug("  Unified old and new RHS;")

            # the newly-generated sub equations are applied to the subs already in ctx
            for key, value in temp_ctx.generic_subs_items():
                key, value = self.sub_in_subs(key, value)
                if key.counter not in self.generic_subs:
                    self._store_new_sub(key, value)

            logging.debug(f"Ended insertion of {generic_type} ~~> {new_type} in CTX")

        else:
            # in each already-known sub in ctx, apply substitution described by the new sub
            logging.debug(f"  LHS was not found in ctx, proceding")
            generic_type, new_type = self.sub_in_subs(generic_type, new_type)
            self._store_new_sub(generic_type, new_type)  # self.generic_subs[generic_type] = new_type
            logging.debug(f"Ended insertion of {generic_type} ~~> {new_type} in CTX")



    def sub_in_subs(self, generic: ZTGeneric, new: ZType) -> tuple[ZTGeneric, ZType]:
        """
        For each sub (A ~~> B) in Context, apply in B the substitution in the argument.
        Performs all the needed occur check after the substitution is applied.
        :param generic:
        :param new:
        :return:
        """
        for key, value in self.generic_subs_items():
            __old_sub_only_for_debug = copy.deepcopy(value)

            if key.counter in [64, 68]:
                print("lol")

            # update old sub
            self._store_new_sub(
                key,
                value.substitute_generic(generic, new)
            )
            # self.generic_subs[key] = value.substitute_generic(generic, new)
            logging.debug(f"    Transformed {__old_sub_only_for_debug} into {self.rhs_of_sub(key)}")

            # occur check on newly created sub
            if key in self._find_generics_inside(self.rhs_of_sub(key)):
                raise Exception(
                    f"OCCUR CHECK FAIL\n" +
                    f"After applying the new, possibly refined, candidate substitution:\n" +
                    f"\t{generic} ~~> {new}\n" +
                    f"The old substitution already found in context:\n" +
                    f"\t{key} ~~> {__old_sub_only_for_debug}\n" +
                    f"Became:\n" +
                    f"\t{key} ~~> {self.rhs_of_sub(key)}\n" +
                    "Which fails the occur check."
                )

            # If, in ctx, you have a sub like:
            #    (R1)  a ~~> u16
            # and your new sub is like:
            #    (R2)  x ~~> (a -> u8)
            # you must also perform substitution in R2 using R1, obtaining
            #    (R2') x ~~> u16 -> u8
            new = new.substitute_generic(key, self.rhs_of_sub(key)) # self.generic_subs[key])

            # occur check on the updated candidate sub
            if generic in self._find_generics_inside(new):
                raise Exception(
                    f"OCCUR CHECK FAIL\n" +
                    f"The (possibly refined) candidate substitution:\n" +
                    f"\t{generic} ~~> {new}\n" +
                    "fails the occur check."
                )

        return generic, new


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


    def ordered_subs(self) -> Tuple[Dict[int, ZType], List[ZTGeneric]]:
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

        for generic, sub_type in self.generic_subs_items():
            dependency_graph.add_node(generic)

            for neigh in self._find_generics_inside(sub_type):
                dependency_graph.add_edge(generic, neigh)
                logging.debug(f"From {generic} ~~> {sub_type}: added to graph: {generic} ==> {neigh}")


        return self.generic_subs, dependency_graph.ordered_visit()
        # return self.generic_subs, list(self.generic_subs.keys())