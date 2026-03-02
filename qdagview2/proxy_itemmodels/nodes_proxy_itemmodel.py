from __future__ import annotations
from typing import *

from PyQt6.QtCore import QObject
from qtpy.QtGui import *
from qtpy.QtCore import *

from qdagview2.models.graph_references import (
    NodeRef, OutletRef, InletRef, LinkRef)
from qdagview2.models.abstract_graph_model import AbstractGraphModel

import bidict


class NodesProxyItemModel(QAbstractItemModel):
    sourceModelChanged = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._source_model:AbstractGraphModel|None = None
        self._connections = []
        self._node_to_row = bidict.bidict[NodeRef, int]()

    def index(self, row, column, parent=None):
        return self.createIndex(row, column)
    
    def parent(self, child: QModelIndex = QModelIndex()) -> QModelIndex:
        # A flat list has no hierarchy; all items are top-level
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid() or self._source_model is None:
            return 0 # List items don't have children
        return len(self._node_to_row) # Use internal map for consistency

    def columnCount(self, parent=None):
        if not self._source_model:
            return 0
        
        if not parent.isValid():
            return self._source_model.nodeColumnsCount()
        else:
            return 0 # No child items, so no columns

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or self._source_model is None:
            return None
            
        if role == Qt.ItemDataRole.DisplayRole:
            # Get the NodeRef from our bidict using the row number
            node_ref = self._node_to_row.inverse.get(index.row())
            if not node_ref:
                return None

            return self._source_model.nodeData(node_ref, index.column(), role)

        return None
            
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
        ...

    def sourceModel(self):
        return self._source_model

    def headerData(self, section, orientation, role=None):
        if self._source_model is None:
            return None
        match orientation:
            case Qt.Orientation.Horizontal:
                return self._source_model.nodeHeaderData(section, role)
            case Qt.Orientation.Vertical:
                return str(section)
