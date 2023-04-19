from typing import *

from forfait.parser.parser_exceptions import ZParserError
from forfait.ztypes.ztypes import ZType, ZTBase


def parse_base_type(s: str) -> ZType:
    match s.strip():
        case "U8": return ZTBase.U8
        case "U16": return ZTBase.U16
        case "BOOL": return ZTBase.BOOL
        case _: raise ZParserError("Can't parse alleged simple type: {s}")
