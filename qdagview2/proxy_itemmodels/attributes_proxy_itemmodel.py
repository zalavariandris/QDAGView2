from __future__ import annotations
from typing import *

from PyQt6.QtCore import QObject
from qtpy.QtGui import *
from qtpy.QtCore import *

from qdagview2.models.graph_references import (
    NodeRef, OutletRef, InletRef, LinkRef)
from qdagview2.models.abstract_graph_model import AbstractGraphModel

import bidict

from qdagview2.models.graph_references import AttributeRef


class AttributesProxyItemModel(QAbstractItemModel):
    sourceModelChanged = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._source_model: AbstractGraphModel | None = None
        self._connections = []
        self._node_to_row = bidict.bidict() # Maps NodeRef to row index
        self._attr_cache: Dict[NodeRef, List[AttributeRef]] = {}  # prevents GC of internal pointers

    def columnCount(self, parent=None):
        return 2

 
    def setSourceModel(self, source_model: AbstractGraphModel):
        # 1. Disconnect from the OLD model first
        if hasattr(self, "_source_model") and self._source_model is not None:
            for signal, slot in self._connections:
                try:
                    signal.disconnect(slot)
                except TypeError: # Handle cases where it's already disconnected
                    pass
        
        # 2. Update reference
        self._source_model = source_model
        self.sourceModelChanged.emit()

        # 3. Connect to the NEW model
        if source_model is not None:
            self.beginResetModel()
            self._node_to_row = bidict.bidict()
            self._attr_cache = {}
            
            # Pre-populate if the model already has nodes
            for i, node in enumerate(source_model.nodes()):
                self._node_to_row[node] = i

            self._connections = [
                (source_model.nodesAboutToBeInserted, self.onNodesAboutToBeInserted),
                (source_model.nodesInserted, self.onNodesInserted), # Use corrected name
                (source_model.nodesAboutToBeRemoved, self.onNodesAboutToBeRemoved),
                (source_model.nodesRemoved, self.onNodesRemoved)
            ]
            for signal, slot in self._connections:
                signal.connect(slot)
                
            self.endResetModel()
        else:
            self._node_to_row = {}
            self._attr_cache = {}

    def onNodesAboutToBeInserted(self, node_refs:List[NodeRef]):
        count = len(self._node_to_row)
        self.beginInsertRows(QModelIndex(), count, count + len(node_refs) - 1)
        for i, node_ref in enumerate(node_refs):
            self._node_to_row[node_ref] = count + i
        print(f"Inserted nodes: {[str(ref) for ref in node_refs]} at rows {count} to {count + len(node_refs) - 1}")

    def onNodesInserted(self, node_refs:List[NodeRef]):
        self.endInsertRows()
        print(f"Finished inserting nodes: {[str(ref) for ref in node_refs]}")

    def onNodesAboutToBeRemoved(self, node_refs: List[NodeRef]):
        # Get current row indices and sort them DESCENDING
        rows_to_remove = sorted([self._node_to_row[ref] for ref in node_refs], reverse=True)
        
        i = 0
        while i < len(rows_to_remove):
            last = rows_to_remove[i]
            first = last
            
            # Find contiguous range
            while i + 1 < len(rows_to_remove) and rows_to_remove[i+1] == first - 1:
                first = rows_to_remove[i+1]
                i += 1
                
            count_removed = (last - first) + 1
            self.beginRemoveRows(QModelIndex(), first, last)
            
            # Remove the deleted nodes from the mapping
            for ref in node_refs:
                # Check if this specific node was part of the range we just told Qt about
                if ref in self._node_to_row and first <= self._node_to_row[ref] <= last:
                    del self._node_to_row[ref]
                    self._attr_cache.pop(ref, None)
                    
            # Shift all remaining rows (the ones that weren't deleted)
            # We use list() because we are modifying the dict values during iteration
            for ref in self._node_to_row:
                if self._node_to_row[ref] > last:
                    self._node_to_row[ref] -= count_removed
                    
            self.endRemoveRows()
            
            # Increment to the next item after the block we just processed
            i += 1

    def onNodesRemoved(self, node_refs: List[NodeRef]):
        # Since we handled begin/end in the "AboutTo" method, 
        # this might be empty or used for final cleanup.
        pass

    def onAttributesChanged(self, item_ref, attribute_name):
        # Invalidate cached attributes so they're re-fetched on next access
        if isinstance(item_ref, NodeRef):
            self._attr_cache.pop(item_ref, None)

    def sourceModel(self):
        return self._source_model

    def headerData(self, section, orientation, role=None):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return "Node"
            elif section == 1:
                return "Value"
        return None

## ----------

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            # This is a Top-Level Node
            node_ref = self._node_to_row.inverse.get(row)
            if node_ref is None:
                return QModelIndex()
            return self.createIndex(row, column, node_ref)
        else:
            # This is an Attribute (Child)
            parent_node = parent.internalPointer()
            # Cache attribute refs to prevent garbage collection of internal pointers
            if parent_node not in self._attr_cache:
                self._attr_cache[parent_node] = self._source_model.attributes(parent_node)
            attrs = self._attr_cache[parent_node]
            if row < len(attrs):
                return self.createIndex(row, column, attrs[row])
        
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        ptr = index.internalPointer()

        # If the pointer is an AttributeRef, its parent is a NodeRef
        if isinstance(ptr, AttributeRef):
            # We need to find the row of the parent node to return its index
            parent_node_ref = ptr._owner
            row = self._node_to_row.get(parent_node_ref)
            if row is not None:
                return self.createIndex(row, 0, parent_node_ref)
        
        # If it's a NodeRef or anything else, the parent is the Root
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        if self._source_model is None:
            return 0
        
        if not parent.isValid():
            # Root level: Number of nodes
            return len(self._node_to_row)
        
        ptr = parent.internalPointer()
        if isinstance(ptr, NodeRef):
            # Node level: Number of attributes for this specific node
            return len(self._source_model.attributes(ptr))
        
        # Attribute level: Attributes don't have children
        return 0

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or self._source_model is None:
            return None
            
        ptr = index.internalPointer()
        
        if role == Qt.ItemDataRole.DisplayRole:
            # LEVEL 1: The Node
            if isinstance(ptr, NodeRef):
                if index.column() == 0:
                    return ptr._name
                return "Node" # Column 1 for nodes
                
            # LEVEL 2: The Attribute
            elif isinstance(ptr, AttributeRef):
                if index.column() == 0:
                    return ptr._name # Attribute Name
                elif index.column() == 1:
                    # Retrieve actual value from the source model
                    return str(self._source_model.attributeData(ptr))
                    
        return None