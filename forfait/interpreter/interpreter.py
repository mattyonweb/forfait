import traceback

from forfait.astnodes import AstNode, Quote, Number, Funcall, Funcdef, Sequence, Boolean
from forfait.parser import Parser, ZUnknownFunction
from forfait.stdlibs.basic_stdlib import STDLIB
from forfait.ztypes.context import Context

class Interpreter:
    def __init__(self, ctx: Context):
        self.ctx = ctx

        self.memory = dict()
        self.dictionary = dict()
        self.stack = list()

    def clear(self):
        self.ctx.clear_generic_subs()
        self.memory = dict()
        self.dictionary = dict()
        self.stack = list()

    def eval(self, s: str):
        for node in Parser(self.ctx).parse(s):
            self.eval_astnode(node)

    def eval_astnode(self, node: AstNode):
        if isinstance(node, Sequence):
            for x in node.funcs:
                self.eval_astnode(x)
        elif isinstance(node, Number):
            self.stack.append(node.n)
        elif isinstance(node, Boolean):
            self.stack.append(node.b)
        elif isinstance(node, Quote):
            self.stack.append(lambda: self.eval_astnode(node.body))
        elif isinstance(node, Funcdef):
            self.dictionary[node.funcname] = node.funcbody
        elif isinstance(node, Funcall):
            if node.funcname in self.dictionary:
                self.eval_astnode(self.dictionary[node.funcname])
            else:
                self.eval_builtin(node.funcname)

    def eval_builtin(self, s: str):
        match s:
            case "swap":
                a, b = self.stack.pop(), self.stack.pop()
                self.stack.append(a)
                self.stack.append(b)
            case "drop":
                self.stack.pop()
            case "dup":
                x = self.stack.pop()
                self.stack.append(x)
                self.stack.append(x)
            case "over":
                self.stack.append(self.stack[-2])
            case "inc-8bit":
                self.stack.append((self.stack.pop() + 1) % 256)
            case "inc-16bit":
                self.stack.append((self.stack.pop() + 1) % 65536)
            case "dec-8bit":
                self.stack.append((self.stack.pop() - 1) % 256)
            case "dec-16bit":
                self.stack.append((self.stack.pop() - 1) % 65536)
            case "if":
                if self.stack.pop():
                    self.stack.pop()
                else:
                    temp = self.stack.pop()
                    self.stack.pop()
                    self.stack.append(temp)
            case "indexed-iter":
                quoted_foo = self.stack.pop()  # è una lambda
                end, start = self.stack.pop(), self.stack.pop()
                for i in range(start, end):
                    self.stack.append(i % 256)
                    quoted_foo()
            case "+u8":
                self.stack.append(((self.stack.pop() % 256) + (self.stack.pop() % 256)) % 256)
            case "-u8":
                self.stack.append(((self.stack.pop() % 256) - (self.stack.pop() % 256)) % 256)
            case "*u8":
                self.stack.append(((self.stack.pop() % 256) * (self.stack.pop() % 256)) % 256)
            case "/u8":
                self.stack.append(((self.stack.pop() % 256) // (self.stack.pop() % 256)) % 256)
            case ">u8":
                self.stack.append(((self.stack.pop() % 256) > (self.stack.pop() % 256)))
            case "<u8":
                self.stack.append(((self.stack.pop() % 256) < (self.stack.pop() % 256)))
            case ">=u8":
                self.stack.append(((self.stack.pop() % 256) >= (self.stack.pop() % 256)))
            case "<=u8":
                self.stack.append(((self.stack.pop() % 256) <= (self.stack.pop() % 256)))
            case "==u8":
                self.stack.append(((self.stack.pop() % 256) == (self.stack.pop() % 256)))
            case "!=u8":
                self.stack.append(((self.stack.pop() % 256) != (self.stack.pop() % 256)))
            case "u16":
                pass
            case "store-at":
                address = self.stack.pop()
                obj = self.stack.pop()
                assert isinstance(obj, int) and 0 <= obj <= 256
                self.memory[address] = obj
            case "eval":
                self.stack.pop()()
            case "__clear":
                self.clear()
            case ":s":
                print(self.stack)


if __name__ == "__main__":
    import logging
    import readline

    logging.basicConfig(level=logging.INFO)

    I = Interpreter(STDLIB)
    while True:
        s = input(">>> ")
        if s.strip() == "":
            continue
        try:
            I.eval(s)
        except ZUnknownFunction as e:
            print(traceback.format_exc())
            continue