from typing import *

from forfait.my_exceptions import ZException

class ZParserError(ZException):
    pass
class ZEmptyFile(ZParserError):
    pass
class ZUnknownFunction(ZParserError):
    pass
class ZNoEndToFuncDef(ZParserError):
    pass
class ZForbiddenNestedFuncdef(ZParserError):
    pass