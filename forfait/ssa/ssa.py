# from typing import *

from forfait.astnodes import Funcall, Sequence, Number, Quote, Boolean, ZConstant
from forfait.ztypes.ztypes import ZType, ZTBase, ZTFunc, ZTGeneric, ZTFunction


class Register:
    counter: int = 0

    def __init__(self, t: ZType):
        self.i = Register.counter
        self.type = t

        Register.counter += 1

    def __str__(self):
        return f"R{self.i} :: {self.type}"


class Phi(Register):
    def __init__(self, t: ZType, r1: Register, r2: Register):
        super().__init__(t)
        self.r1 = r1
        self.r2 = r2

    def __str__(self):
        return f"Φ{self.i}({self.r1}, {self.r2}) :: {self.type}"

##############################

def is_constant(x: Register | Funcall | Quote | Number):
    return isinstance(x, Number)

class SSA_Instr:
    pass

class SSA_Constant(SSA_Instr):
    def __init__(self, r: Register, c: ZConstant):
        self.r = r
        self.const = c
    def __str__(self):
        return f"({self.r}) <- {self.const}"

class SSA_Copy(SSA_Instr):
    def __init__(self, r: Register, src_reg: Register):
        self.r = r
        self.src_reg = src_reg
    def __str__(self):
        return f"({self.r}) <- ({self.src_reg})"

class SSA_Cast(SSA_Instr):
    def __init__(self, new_reg: Register, old_reg: Register, new_type: ZType):
        self.new_reg = new_reg
        self.old_reg = old_reg
        self.new_type = new_type
    def __str__(self):
        return f"({self.new_reg}) <- ({self.new_type}) ({self.old_reg})"

class SSA_Quote(SSA_Instr):
    def __init__(self, reg: Register, quote: Quote):
        self.r = reg
        self.quote = quote
    def __str__(self):
        return f"({self.r}) <- ({self.quote})"

class SSA_Binop(SSA_Instr):
    def __init__(self, r: Register, func: Funcall, op1, op2):
        self.r = r
        self.func = func
        self.op1 = op1
        self.op2 = op2

    def __str__(self):
        return f"({self.r}) <- {self.func.funcname}({self.op1}, {self.op2})"

    def defacto_constant(self) -> bool:
        return is_constant(self.op1) and is_constant(self.op2)

    def calculate_constant(self) -> ZConstant:
        # TODO: optimizations on boolean functions e.g. AND
        assert isinstance(self.op1, Number)
        assert isinstance(self.op2, Number)

        arg1 = self.op1.n % (65536 if self.op1.type.right.types[-1] == ZTBase.U16 else 256)
        arg2 = self.op2.n % (65536 if self.op2.type.right.types[-1] == ZTBase.U16 else 256)

        funcname = self.func.funcname

        if funcname in ["+u8", "+u16"]:
            out = (arg1 + arg2) % (65536 if self.func.type.right.types[-1] == ZTBase.U16 else 256)
        elif funcname in ["-u8", "-u16"]:
            out = (arg1 - arg2) % (65536 if self.func.type.right.types[-1] == ZTBase.U16 else 256)
        elif funcname in ["*u8", "*u16"]:
            out = (arg1 * arg2) % (65536 if self.func.type.right.types[-1] == ZTBase.U16 else 256)
        elif funcname in ["/u8", "/u16"]:
            out = (arg1 // arg2) % (65536 if self.func.type.right.types[-1] == ZTBase.U16 else 256)
        elif funcname in ["<=u8", "<=u16"]:
            return Boolean(arg1 <= arg2)
        elif funcname in ["<u8", "<u16"]:
            return Boolean(arg1 < arg2)
        elif funcname in [">=u8", ">=u16"]:
            return Boolean(arg1 >= arg2)
        elif funcname in [">u8", ">u16"]:
            return Boolean(arg1 > arg2)
        elif funcname in ["==u8", "==u16"]:
            return Boolean(arg1 == arg2)
        else:
            # TODO: trasformarlo in logger.info()
            raise Exception(f"Can't perform constant propagation on:\n\t{self}\nbecause this optimization is not implemented for function: {self.func}")

        return Number(out, self.func.type.right.types[-1])


class SSA_Jump(SSA_Instr):
    def __init__(self, test_reg: Register, if_true_jump_to: "CFG", else_jump_to: "CFG"):
        self.test_reg = test_reg
        self.jump_to = if_true_jump_to
        self.else_jump_to = else_jump_to
    def __str__(self):
        return f"if ({self.test_reg}) goto {self.jump_to.human_friendly_name()}; else goto {self.else_jump_to.human_friendly_name()}"

##############################################

class CFG:
    counter = 0

    def __init__(self, notes:str=""):
        self.notes = notes # for debuggin porpusoes
        self.numeric_id = CFG.counter # for debugin porupes
        CFG.counter += 1

        self.instructions: list[SSA_Instr] = list()
        self.final_vstack: list[Register] = list()

        self.entering_cfgs: list["CFG"] = list()
        self.exiting_cfgs: list["CFG"] = list()

    def set_cfg(self, instructions: list[SSA_Instr], final_vstack: list[Register]):
        self.instructions += instructions
        self.final_vstack = final_vstack

    def add_entering_cfg(self, other_cfg: "CFG"):
        self.entering_cfgs.append(other_cfg)

    def add_exiting_cfg(self, other_cfg: "CFG"):
        self.exiting_cfgs.append(other_cfg)

    def set_note(self, s: str):
        self.notes = s

    def visit(self, callable):
        callable(self)
        for cfg in self.exiting_cfgs:
            cfg.visit(callable)

    def graph_visit(self):
        # preorder
        to_visit = [self]
        visited  = set()

        while len(to_visit) > 0:
            cfg = to_visit.pop()
            if cfg in visited:
                continue
            yield cfg
            visited.add(cfg)
            for exit in cfg.exiting_cfgs:
                to_visit.append(exit)

    def emit_program(self) -> str:
        out = str()
        for cfg in self.graph_visit():
            out += f"{cfg.machine_friendly_name()}:\n"
            for i in cfg.instructions:
                out += f"\t{i}\n"
            out += "\n"
        return out

    def machine_friendly_name(self) -> str:
        return f"CFG_{self.numeric_id}"

    def human_friendly_name(self):
        return f"{self.machine_friendly_name()} " + self.notes

    def __str__(self):
        s = "\n+ ================================================ +\n"
        s += f"Block named: {self.human_friendly_name()}\n"
        for i in self.instructions:
            s += f"\t{i}\n"

        s += "Final vstack:\n"
        s += f"\t{', '.join(str(x) for x in self.final_vstack)}\n"

        s += "Branches out to:\n"
        s += f"\t{','.join(x.human_friendly_name() for x in self.exiting_cfgs)}\n"
        return s

########################################################

def most_concrete_type(t1: ZType, t2: ZType):
    # calculates concrete type in case a register has to be assigned one of two non-equal types.
    # raises exception when types can't be "unified"
    # that raises the question: is SSAify the correct place to perform this monomoprihization?
    if isinstance(t1, ZTGeneric) and isinstance(t2, ZTGeneric):
        raise Exception(f"Two generic types: {t1} and {t2}")
    if isinstance(t2, ZTGeneric):
        return most_concrete_type(t2, t1)
    if isinstance(t1, ZTGeneric):
        return t2
    # in case they are both concrete
    if t1 == t2:
        return t2
    raise Exception(f"Two concrete types, impossible to 'unify': {t1} and {t2}")

mcu = most_concrete_type

VStack = list[Register]

def SSA_ification(astnode: Sequence, start_vstack:VStack=None) -> tuple[CFG, VStack]:
    """
    Given an `Astnode` `Sequence`, calculates its SSA representation.

    Basically the idea is to linearize a given stack-based program, by building a register-based representation
    of the program.

    This is done by simulating the execution of the code, where instead of putting _values_ on the stack,
    we put _registers_. This "virtual stack" is called vstack.

    :param astnode: `Astnode` to transform
    :param start_vstack: Used in nested calls of this function: when a block requires some elements already on
    the stack, they will be found here.
    :return:
    """
    assert isinstance(astnode, Sequence), "sissify only for sequences atm"

    vstack:  VStack          = list() if start_vstack is None else start_vstack
    program: list[SSA_Instr] = list()

    start_cfg: CFG = CFG()
    curr_cfg:  CFG = start_cfg

    for funcall in astnode.funcs:

        # a Number is converted to a simple constant assignment to a newly-created register
        if isinstance(funcall, Number):
            reg = Register(funcall.typeof(None).right.types[-1])

            program.append( SSA_Constant(reg, funcall) )
            vstack.append( reg )

        # a Quote is stored unchanged for future uses
        elif isinstance(funcall, Quote):
            reg = Register(funcall.type)

            program.append(SSA_Quote(reg, funcall))
            vstack.append(reg)


        elif isinstance(funcall, Funcall):
            match funcall.funcname:
                case "dup":
                    # dup may reach this point while still generic; this has to be handled
                    # regtype = mcu(
                    #     funcall.type.right.types[-1],  # calculated type (may still be generic)
                    #     vstack[-1].type                # concrete type, calculated via simulated execution
                    # )

                    reg = Register(funcall.type.right.types[-1])

                    program.append( SSA_Copy(reg, vstack[-1]) )
                    vstack.append( reg )

                case "drop":
                    vstack.pop()

                case "swap":
                    fst: Register = vstack.pop()
                    snd: Register = vstack.pop()

                    reg_temp = Register(snd.type) # copy snd in temp
                    program.append( SSA_Copy(reg_temp, snd) )

                    reg_new_snd = Register(fst.type) # copy fst in snd
                    program.append( SSA_Copy(reg_new_snd, fst))

                    reg_new_fst = Register(snd.type) # copy temp in fst
                    program.append(SSA_Copy(reg_new_fst, reg_temp))

                    vstack.append(reg_new_snd)
                    vstack.append(reg_new_fst)

                case "u16":
                    reg = Register(funcall.type.right.types[-1]) # ie. u16
                    program.append( SSA_Cast(reg, vstack.pop(), funcall.type.right.types[-1]))
                    vstack.append(reg)

                case "if":
                    # extract `else` quotation
                    _else_reg = vstack.pop()
                    else_ssa_instr = program.pop()
                    assert isinstance(else_ssa_instr, SSA_Quote)

                    # extract `then` quotation
                    _then_reg = vstack.pop()
                    then_ssa_instr = program.pop()
                    assert isinstance(then_ssa_instr, SSA_Quote)

                    # register containing boolean value
                    cond_reg = vstack.pop()
                    assert cond_reg.type == ZTBase.BOOL

                    # visit `then` and `else` quotations; for each, build instructions and vstack
                    import copy
                    then_cfg, then_vstack = SSA_ification(then_ssa_instr.quote.body, copy.copy(vstack))
                    else_cfg, else_vstack = SSA_ification(else_ssa_instr.quote.body, copy.copy(vstack))

                    # add, as last instruction to current CFG, the jump SSA instruction
                    program.append(SSA_Jump(cond_reg, then_cfg, else_cfg))

                    curr_cfg.add_exiting_cfg(then_cfg)
                    curr_cfg.add_exiting_cfg(else_cfg)
                    then_cfg.add_entering_cfg(curr_cfg)
                    else_cfg.add_entering_cfg(curr_cfg)

                    # finalize current CFG
                    curr_cfg.instructions += program
                    curr_cfg.final_vstack = vstack
                    program = list()
                    vstack  = list()

                    # create new CFG
                    curr_cfg = CFG()
                    curr_cfg.add_entering_cfg(then_cfg)
                    curr_cfg.add_entering_cfg(else_cfg)
                    then_cfg.add_exiting_cfg(curr_cfg)
                    else_cfg.add_exiting_cfg(curr_cfg)

                    # create phi nodes in new CFG
                    assert len(then_vstack) == len(else_vstack), "if branches return different num of args!"
                    for i, (r1, r2) in enumerate(zip(then_vstack, else_vstack)):
                        if r1.type != r2.type or isinstance(r1.type, ZTGeneric) or isinstance(r2.type, ZTGeneric):
                            # controlla i tipi teorici calcolati in then_ssa_instr.quote
                            # e mettici quelli (in teoria potresti su ogni ciclo dell'iterazione... da cambiare TODO)
                            # unquoted_rhs_then: ZTFunction = then_ssa_instr.quote.type.right.types[0]
                            # then_candidate_type = unquoted_rhs_then.right.types[i]
                            #
                            # unquoted_rhs_else: ZTFunction = else_ssa_instr.quote.type.right.types[0]
                            # else_candidate_type = unquoted_rhs_else.right.types[i]
                            #
                            # assert then_candidate_type == else_candidate_type, f"{r1}, {r2} and {then_candidate_type}, {else_candidate_type}"
                            #
                            # vstack.append(Phi(then_candidate_type, r1, r2))
                            assert r1.type == r2.type, f"{r1}, {r2}"
                        vstack.append(Phi(r1.type, r1, r2))
                case _:
                    if funcall.funcname in ["+u8", "-u8", "*u8", "/u8", "+u16", "-u16", "*u16", "/u16",
                                            "<u8", "<=u8", ">u8", ">=u8", "<u16", "<=u16", ">u16", ">=u16"]:
                        reg = Register(funcall.type.right.types[-1])
                        snd = vstack.pop()
                        fst = vstack.pop()
                        program.append(SSA_Binop(reg, funcall, fst, snd))
                        vstack.append(reg)
                    else:
                        raise Exception(f"Not yet implemented: SSAfication of funcall {funcall}")

        else:
            raise Exception("Unknwon astnode type")

    curr_cfg.instructions += program
    curr_cfg.final_vstack = vstack

    return start_cfg, vstack


def constant_propagation(start_cfg: CFG) -> CFG:
    """
    Applies the constant propagation optimization on all CFGs reachable from a given CFG.
    :param start_cfg: The first block to optimize
    :return: The starting CFG after the optimization
    """
    subs: dict[Register, Funcall] = dict()

    for cfg in start_cfg.graph_visit():
        new_subs = constant_propagation_single_cfg(cfg, subs)
        subs |= new_subs

    return start_cfg


def constant_propagation_single_cfg(cfg: CFG, subs: dict[Register, Funcall]) -> dict[Register, Funcall]:
    """
    Constant propagation for a _single_ CFG.
    :param cfg:
    :param subs: Dictionary of constant registers found so far
    :return: Dictionary of constant register found so far, after this round of optimization
    """
    for i, instr in enumerate(cfg.instructions):
        if isinstance(instr, SSA_Constant):
            subs[instr.r] = instr.const

        elif isinstance(instr, SSA_Binop):
            if instr.op1 in subs:
                instr.op1 = subs[instr.op1]
            if instr.op2 in subs:
                instr.op2 = subs[instr.op2]

            if instr.defacto_constant():
                const = instr.calculate_constant()
                cfg.instructions[i] = SSA_Constant(instr.r, const)
                subs[instr.r] = const

        elif isinstance(instr, SSA_Copy):
            if instr.src_reg in subs:
                cfg.instructions[i] = SSA_Constant(instr.r, subs[instr.src_reg])

        else:
            pass # TODO

    return subs