from pathlib import Path


class Compiler:
    def __init__(self):
        pass

    def compile_source_code(self, source: str):
        untyped_ast = Parser().parse(source)
        typed_ast   = Typechecker().type_ast(untyped_ast)