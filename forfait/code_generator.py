from typing import *

from forfait.astnodes import AstNode


class CodeGenerator:
    def __init__(self, ctx):
        self.ctx = ctx

    def generate(self, optimized_ast: AstNode):
        return optimized_ast.asm()
