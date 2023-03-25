from typing import List

from forfait.astnodes import AstNode, Funcall, Funcdef, Sequence, Quote, Number, Boolean
from forfait.my_exceptions import ZException
from forfait.stdlibs.basic_stdlib import STDLIB
from forfait.ztypes.context import Context
from forfait.ztypes.ztypes import ZTBase

import logging
logging.basicConfig(level=logging.DEBUG)

class ZParserError(ZException):
    pass
class ZEmptyFile(ZParserError):
    pass
class ZUnknownFunction(ZParserError):
    pass
class ZNoEndToFuncDef(ZParserError):
    pass

class Parser:
    """
    Class that parses and performs typechecking on raw source code.
    """
    def __init__(self, ctx: Context):
        self.ctx = ctx

    def parse(self, code: str) -> List[AstNode]:
        """ Entry point for parsing. """
        tokens = self.tokenize(code)
        nodes  = self.parse_tokens(tokens)
        for n in nodes:
            n.typecheck(self.ctx)
            n.typeof(self.ctx)
        return nodes

    ##################################################

    def tokenize(self, code: str) -> List[str]:
        """
        Splits source code in a list of funcalls
        """
        funcalls: List[str]  = list()
        for line in code.split("\n"):
            funcalls += [foo for foo in line.strip().split(" ") if foo != ""]
        return funcalls


    def parse_tokens(self, tokens: List[str]) -> List[AstNode]:
        """
        Procedure for interpreting the meaning of each token
        """
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

        return self.compress_ast(ast)


    def parse_funcall(self, funcname: str) -> Funcall:
        if funcname in self.ctx.builtin_types:
            return Funcall(funcname, self.ctx.get_builtin_type(funcname))
        if funcname in self.ctx.user_types:
            return Funcall(funcname, self.ctx.get_userdefined_type(funcname))
        if funcname in ["true", "false"]:
            return Boolean(funcname == "true")

        try:
            return Number(int(funcname), ZTBase.U8)  # TODO: type of integers
        except ValueError:
            pass

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

        assert len(ast) == 1 and isinstance(ast[0], Sequence), " ".join([str(s) for s in ast])
        # assert all(isinstance(n, Funcall) for n in ast), " ".join([str(s) for s in ast])

        # funcdef_obj = Funcdef(funcname, Sequence(ast))
        funcdef_obj = Funcdef(funcname, ast[0])
        self.ctx.user_types[funcname] = funcdef_obj.typeof(self.ctx)

        return funcdef_obj


    def parse_quotation(self, tokens) -> Quote:
        depth = 1
        quote_block = list()

        while not (depth == 1 and tokens[0] == "|]"):
            t = tokens.pop(0)
            quote_block.append(t)

            match t:
                case "[|":
                    depth += 1
                case "|]":
                    depth -= 1
                    if depth <= 0:
                        raise ZParserError("Found '|]' without relative '[|'")
                case _:
                    pass

        tokens.pop(0)  # removes |]

        # avoid Sequence { Sequence { ... } } problem
        parsed_body = self.compress_ast(self.parse_tokens(quote_block))
        if len(parsed_body) == 1 and isinstance(parsed_body[0], Sequence):
            return Quote(parsed_body[0])
        else:
            return Quote(Sequence(self.parse_tokens(quote_block)))


    def compress_ast(self, l: List[AstNode]):
        """
        Transforms a list of consecutive Funcalls into a Sequence
        """
        out = list()
        temp = list()
        for f in l:
            if isinstance(f, Funcall):
                temp.append(f)
            else:
                if len(temp) > 0:
                    out.append(Sequence(temp))
                    temp = []
                out.append(f)

        if len(temp) > 0:
            out.append(Sequence(temp))
        return out

if __name__ == "__main__":
    s = """
    : square dup *u8 ;
    0 5 
      [| dup [| 1 |] eval drop u16 store-at |]  indexed-iter 
    """
    for x in Parser(STDLIB).parse(s):
        print(x.prettyprint())
        # print(f"{type(x)}\t\t~~>\t {x}\t\t{x.typeof(STDLIB)}", end="\n")

    print(x.typeof(STDLIB))

    def sequence_from_str(s):
        return Parser(STDLIB).parse(s)

    print(sequence_from_str("0 5 10")[0].typeof(STDLIB))
