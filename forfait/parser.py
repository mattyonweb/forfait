from typing import List

class Parser:
    def parse(self, code: str) -> List[str]:
        funcalls: List[str]  = list()
        for line in code.split("\n"):
            funcalls += [foo for foo in line.strip().split(" ") if foo != ""]
        return funcalls