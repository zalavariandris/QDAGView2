from typing import Hashable

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class NodeRef:
    name: Hashable
    def isValid(self):
        return self.name != ""

@dataclass(frozen=True, slots=True)
class InletRef:
    node: NodeRef
    name: Hashable
    def isValid(self):
        return self.node.isValid() and self.name != ""

@dataclass(frozen=True, slots=True)
class OutletRef:
    node: NodeRef
    name: Hashable
    def isValid(self):
        return self.node.isValid() and self.name != ""

@dataclass(frozen=True, slots=True)
class LinkRef:
    source: OutletRef
    target: InletRef
    name: Hashable
    def isValid(self):
        return self.source.isValid() and self.target.isValid()

@dataclass(frozen=True, slots=True)
class AttributeRef:
    owner: NodeRef|InletRef|OutletRef|LinkRef
    name: Hashable
    def isValid(self):
        return self.owner.isValid() and self.name != ""