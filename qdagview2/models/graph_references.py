from typing import Hashable

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class NodeRef:
    _name: Hashable
    def isValid(self):
        return self._name != ""

    def __str__(self):
        return f"Node({self._name})"

@dataclass(frozen=True, slots=True)
class InletRef:
    _node: NodeRef
    _name: Hashable
    def isValid(self):
        return self._node.isValid() and self._name != ""
    
    def __str__(self):
        return f"In({self._node._name}.{self._name})"

@dataclass(frozen=True, slots=True)
class OutletRef:
    _node: NodeRef
    _name: Hashable
    def isValid(self):
        return self._node.isValid() and self._name != ""
    
    def __str__(self):
        return f"Out({self._node._name}.{self._name})->"

@dataclass(frozen=True, slots=True)
class LinkRef:
    _source: OutletRef
    _target: InletRef
    _name: Hashable
    def isValid(self):
        return self._source.isValid() and self._target.isValid()

    def __str__(self):
        return f"Link({self._source} -> {self._target})"

@dataclass(frozen=True, slots=True)
class AttributeRef:
    _owner: NodeRef|InletRef|OutletRef|LinkRef
    _name: Hashable
    def isValid(self):
        return self._owner.isValid() and self._name != ""

    def __str__(self):
        return f"Attr({self._owner}.{self._name})"