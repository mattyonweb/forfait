from typing import List

from forfait.astnodes import AstNode, Funcall, Funcdef, Sequence, Quote, Number
from forfait.my_exceptions import ZException
from forfait.ztypes.context import Context, STDLIB
from forfait.ztypes.ztypes import ZTBase


class ZParserError(ZException):
    pass
class ZEmptyFile(ZParserError):
    pass
class ZUnknownFunction(ZParserError):
    pass
class ZNoEndToFuncDef(ZParserError):
    pass

class Parser:
    def __init__(self, ctx: Context):
        self.ctx = ctx

    def parse(self, code: str) -> List[AstNode]:
        """ Entry point for parsing """
        tokens = self.tokenize(code)
        nodes  = self.parse_tokens(tokens)
        for n in nodes:
            n.typecheck(self.ctx)
        return nodes

    ##################################################

    def tokenize(self, code: str) -> List[str]:
        funcalls: List[str]  = list()
        for line in code.split("\n"):
            funcalls += [foo for foo in line.strip().split(" ") if foo != ""]
        return funcalls

    def parse_tokens(self, tokens: List[str]) -> List[AstNode]:
        if len(tokens) == 0:
            raise ZEmptyFile("The file does not contain computable expressions.")

        ast: List[AstNode] = list()

        while len(tokens) > 0:
            token = tokens.pop(0)

            match token:
                case "[|":
                    ast.append(self.parse_quotation(tokens))
                case ":":
                    ast.append(self.parse_funcdef(tokens))
                case _:
                    ast.append(self.parse_funcall(token))

        # ast = self.compress_ast(ast)
        return ast


    def parse_funcall(self, funcname: str) -> Funcall:
        if funcname in self.ctx.builtin_types:
            return Funcall(funcname, self.ctx.builtin_types[funcname])
        if funcname in self.ctx.user_types:
            return Funcall(funcname, self.ctx.user_types[funcname])

        try:
            return Number(int(funcname), ZTBase.U8)
        except ValueError:
            raise ZUnknownFunction(funcname)


    def parse_funcdef(self, tokens: List[str]) -> Funcdef:
        try:
            idx = tokens.index(";")  # implies: no nested functions
        except ValueError as e:
            raise ZNoEndToFuncDef(" ".join(tokens))

        # esaurisci il body della funzione
        funcbody_tokens = list()
        for _ in range(idx):
            funcbody_tokens.append(tokens.pop(0))
        tokens.pop(0) # pop del ";"

        # costruisci istanza
        funcname: str      = funcbody_tokens.pop(0)
        ast: List[Funcall] = self.parse_tokens(funcbody_tokens)

        assert(all(isinstance(n, Funcall) for n in ast))

        funcdef_obj = Funcdef(funcname, Sequence(ast))
        self.ctx.user_types[funcname] = funcdef_obj

        return funcdef_obj

    def parse_quotation(self, tokens) -> Quote:
        return None # TODO

if __name__ == "__main__":
    for x in Parser(STDLIB).parse(": myFoo over +u8 +u8 ; 1 3 5 myFoo"):
        print(x, end=" ")

