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
    def __init__(self, t: ZType, r1: Register, r2: Register):
        super().__init__(t)
        self.r1 = r1
        self.r2 = r2

    def __str__(self):
        return f"Φ{self.i}({self.r1}, {self.r2}) :: {self.type}"

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
    def __init__(self, r: Register, func: Funcall, op1, op2):
        self.r = r
        self.func = func
        self.op1 = op1
        self.op2 = op2
    def __str__(self):
        return f"({self.r}) <- {self.func.funcname}({self.op1}, {self.op2})"

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

    def human_friendly_name(self):
        return f"CFG_{self.numeric_id} " + self.notes

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


def sissify(astnode: Sequence, start_vstack:list[Register]=None) -> tuple[CFG, list[Register]]:
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
                    # extract `else` quotation
                    else_reg = vstack.pop()
                    else_ssa_instr = program.pop()
                    assert isinstance(else_ssa_instr, SSA_Quote)

                    # extract `then` quotation
                    then_reg = vstack.pop()
                    then_ssa_instr = program.pop()
                    assert isinstance(then_ssa_instr, SSA_Quote)

                    # register containing boolean value
                    cond_reg = vstack.pop()

                    # visit `then` and `else` quotations; for each, build instructions and vstack
                    import copy
                    then_cfg, then_vstack = sissify(then_ssa_instr.quote.body, copy.copy(vstack))
                    else_cfg, else_vstack = sissify(else_ssa_instr.quote.body, copy.copy(vstack))

                    # then_cfg.set_note("THEN branch of IF")
                    # else_cfg.set_note("ELSE branch of IF")

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
                    # curr_cfg.set_note("After IF branches")
                    curr_cfg.add_entering_cfg(then_cfg)
                    curr_cfg.add_entering_cfg(else_cfg)
                    then_cfg.add_exiting_cfg(curr_cfg)
                    else_cfg.add_exiting_cfg(curr_cfg)

                    # create phi nodes in new CFG
                    assert len(then_vstack) == len(else_vstack), "if branches return different num of args!"
                    for r1, r2 in zip(then_vstack, else_vstack):
                        assert r1.type == r2.type, f"{r1}, {r2}"
                        vstack.append(Phi(r1.type, r1, r2))

                case _:
                    if funcall.funcname in ["+u8", "-u8", "*u8", "/u8", "+u16", "-u16", "*u16", "/u16"]:
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