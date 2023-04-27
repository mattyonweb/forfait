# from typing import *

from forfait.astnodes import Funcall, Sequence, Number, Quote
from forfait.ztypes.ztypes import ZType

class Register:
    counter: int = 0

    def __init__(self, t: ZType):
        self.i = Register.counter
        self.type = t

        Register.counter += 1

    def __str__(self):
        return f"R{self.i} :: {self.type}"


class Phi(Register):
    def __init__(self, i: int, t: ZType, r1: Register, r2: Register):
        super().__init__(i, t)
        self.r1 = r1
        self.r2 = r2

##############################

def auto_str(cls):
    cls.__repr__ = cls.__str__
    return cls

class SSA_Instr:
    pass

class SSA_Constant(SSA_Instr):
    def __init__(self, r: Register, c):
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
    def __init__(self, r: Register, func: Funcall, *operands):
        self.r = r
        self.func = func
        self.operands = operands
    def __str__(self):
        return f"({self.r}) <- {self.func.funcname}({', '.join([str(x) for x in self.operands])})"

##############################################

class CFG:
    def __init__(self, notes:str=""):
        self.notes = notes # for debuggin porpusoes

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

    def visit(self):
        yield self
        for cfg in self.exiting_cfgs:
            yield cfg.visit()

    def __str__(self):
        s = "+ ================================================ +"
        s = f"Block named: {self.notes}\n"
        for i in self.instructions:
            s += f"\t{i}\n"

        s += "Final vstack:\n"
        s += f"\t{', '.join(str(x) for x in self.final_vstack)}\n"

        s += "Branches out to:\n"
        s += f"\t{','.join(x.notes for x in self.exiting_cfgs)}\n"
        return s


def sissify(astnode: Sequence, start_vstack:list[Register]=None) -> CFG:
    assert isinstance(astnode, Sequence), "sissify only for sequences atm"

    vstack:  list[Register]  = list() if start_vstack is None else start_vstack
    program: list[SSA_Instr] = list()

    start_cfg: CFG = CFG()
    curr_cfg: CFG  = start_cfg

    for funcall in astnode.funcs:
        if isinstance(funcall, Number):
            reg = Register(funcall.typeof(None).right.types[-1])

            program.append( SSA_Constant(reg, funcall) )
            vstack.append( reg )


        elif isinstance(funcall, Quote):
            reg = Register(funcall.type)

            program.append(SSA_Quote(reg, funcall))
            vstack.append(reg)


        elif isinstance(funcall, Funcall):
            match funcall.funcname:
                case "dup":
                    reg = Register(funcall.type.right.types[-1])

                    program.append( SSA_Copy(reg, vstack.pop()) )
                    vstack.append( reg )

                case "drop":
                    vstack.pop()

                case "swap":
                    fst: Register = vstack.pop()
                    snd: Register = vstack.pop()

                    reg_temp = Register(snd.type)
                    program.append( SSA_Copy(reg_temp, snd) )

                    reg_new_snd = Register(fst.type)
                    program.append( SSA_Copy(reg_new_snd, fst))

                    reg_new_fst = Register(snd.type)
                    program.append(SSA_Copy(reg_new_fst, reg_temp))

                    vstack.append(reg_new_snd)
                    vstack.append(reg_new_fst)

                case "u16":
                    reg = Register(funcall.type.right.types[-1]) #ie. u16
                    program.append( SSA_Cast(reg, vstack.pop(), funcall.type.right.types[-1]))
                    vstack.append(reg)

                case "<u8":
                    reg = Register(funcall.type.right.types[-1])
                    snd = vstack.pop()
                    fst = vstack.pop()
                    program.append(SSA_Binop(reg, funcall, fst, snd))
                    vstack.append(reg)

                case "if":
                    else_ssa_instr = program.pop()
                    assert isinstance(else_ssa_instr, SSA_Quote)

                    then_ssa_instr = program.pop()
                    assert isinstance(then_ssa_instr, SSA_Quote)

                    cond_ssa_instr = program.pop()
                    assert isinstance(cond_ssa_instr, SSA_Quote)

                    cond_cfg = sissify(cond_ssa_instr.quote.body, vstack)


                    curr_cfg.instructions += program
                    curr_cfg.instructions += cond_cfg.instructions
                    curr_cfg.final_vstack = cond_cfg.final_vstack

                    import copy
                    then_cfg = sissify(then_ssa_instr.quote.body, copy.copy(curr_cfg.final_vstack))
                    else_cfg = sissify(else_ssa_instr.quote.body, copy.copy(curr_cfg.final_vstack))

                    then_cfg.set_note("THEN branch of IF")
                    else_cfg.set_note("ELSE branch of IF")

                    # TODO: create phi nodes

                    curr_cfg.add_exiting_cfg(then_cfg)
                    curr_cfg.add_exiting_cfg(else_cfg)
                    then_cfg.add_entering_cfg(curr_cfg)
                    else_cfg.add_entering_cfg(curr_cfg)

                    curr_cfg = CFG()
                    curr_cfg.set_note("After IF branches")

                    then_cfg.add_exiting_cfg(curr_cfg)
                    else_cfg.add_exiting_cfg(curr_cfg)
                    curr_cfg.add_entering_cfg(then_cfg)
                    curr_cfg.add_entering_cfg(else_cfg)

                case _:
                    raise Exception(f"Not yet implemented: SSAfication of funcall {funcall}")

        else:
            raise Exception("Unknwon astnode type")

    # return program, vstack
    start_cfg.instructions += program
    start_cfg.final_vstack = vstack
    return start_cfg