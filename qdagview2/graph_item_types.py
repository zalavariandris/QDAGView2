from enum import StrEnum

class GraphItemType(StrEnum):
    BASE = "BASE"
    SUBGRAPH = "SUBGRAPH"
    INLET = "INLET"
    OUTLET = "OUTLET"
    NODE = "NODE"
    LINK = "LINK"