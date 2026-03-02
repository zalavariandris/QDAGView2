from __future__ import annotations
from typing import *

from PyQt6.QtCore import QObject
from qtpy.QtGui import *
from qtpy.QtCore import *

from qdagview2.models.graph_references import (
    NodeRef, OutletRef, InletRef, LinkRef)
from qdagview2.models.abstract_graph_model import AbstractGraphModel

import bidict


class LinksProxyItemModel(QAbstractItemModel):
    sourceModelChanged = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._source_model:AbstractGraphModel|None = None
        self._connections = []
        self._ref_to_row = bidict.bidict[LinkRef, int]()

    def index(self, row, column, parent=None):
        return self.createIndex(row, column)
    
    def parent(self, child: QModelIndex = QModelIndex()) -> QModelIndex:
        # A flat list has no hierarchy; all items are top-level
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid() or self._source_model is None:
            return 0 # List items don't have children
        return len(self._ref_to_row) # Use internal map for consistency

    def columnCount(self, parent=None):
        return 3

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or self._source_model is None:
            return None
            
        if role == Qt.ItemDataRole.DisplayRole:
            # Get the GraphRef from our bidict using the row number
            ref = cast(LinkRef, self._ref_to_row.inverse.get(index.row()))
            if not ref:
                return None

            match index.column():
                case 0:
                    return f"{ref._source}"
                case 1:
                    return f"{ref._target}"
                case 2:
                    return f"{ref._name}"
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
            self._ref_to_row = bidict.bidict()
            
            # Pre-populate if the model already has refs
            for i, ref in enumerate(source_model.links()):
                self._ref_to_row[ref] = i

            self._connections = [
                (source_model.linksAboutToBeInserted, self.onRefsAboutToBeInserted),
                (source_model.linksInserted, self.onRefsInserted), # Use corrected name
                (source_model.linksAboutToBeRemoved, self.onRefsAboutToBeRemoved),
                (source_model.linksRemoved, self.onRefsRemoved)
            ]
            for signal, slot in self._connections:
                signal.connect(slot)
                
            self.endResetModel()
        else:
            self._ref_to_row = {}

    def onRefsAboutToBeInserted(self, refs:List[LinkRef]):
        count = len(self._ref_to_row)
        self.beginInsertRows(QModelIndex(), count, count + len(refs) - 1)
        for i, ref in enumerate(refs):
            self._ref_to_row[ref] = count + i
        print(f"Inserted ref: {[str(ref) for ref in refs]} at rows {count} to {count + len(refs) - 1}")

    def onRefsInserted(self, refs:List[LinkRef]):
        self.endInsertRows()
        print(f"Finished inserting refs: {[str(ref) for ref in refs]}")

    def onRefsAboutToBeRemoved(self, refs: List[LinkRef]):
        # Get current row indices and sort them DESCENDING
        rows_to_remove = sorted([self._ref_to_row[ref] for ref in refs], reverse=True)
        
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
            
            # Remove the deleted refs from the mapping
            for ref in refs:
                # Check if this specific ref was part of the range we just told Qt about
                if ref in self._ref_to_row and first <= self._ref_to_row[ref] <= last:
                    del self._ref_to_row[ref]
                    
            # Shift all remaining rows (the ones that weren't deleted)
            # We use list() because we are modifying the dict values during iteration
            for ref in self._ref_to_row:
                if self._ref_to_row[ref] > last:
                    self._ref_to_row[ref] -= count_removed
                    
            self.endRemoveRows()
            
            # Increment to the next item after the block we just processed
            i += 1

    def onRefsRemoved(self, refs: List[LinkRef]):
        # Since we handled begin/end in the "AboutTo" method, 
        # this might be empty or used for final cleanup.
        pass

    def onAttributesChanged(self, item_ref, attribute_name):
        ...

    def sourceModel(self):
        return self._source_model

    def headerData(self, section, orientation, role=None):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Horizontal:
            match section:
                case 0:
                    return "Source"
                case 1:
                    return "Target"
                case 2:
                    return "Name"

        return None
