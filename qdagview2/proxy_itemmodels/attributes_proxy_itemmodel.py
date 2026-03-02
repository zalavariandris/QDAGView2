from __future__ import annotations
from typing import *

from qtpy.QtGui import *
from qtpy.QtCore import *

from qdagview2.models.graph_references import (
    NodeRef, OutletRef, InletRef, LinkRef)
from qdagview2.models.abstract_graph_model import AbstractGraphModel


class NodeAttributeProxy(QAbstractItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._source_model = None
        self._root_node = None # The specific NodeRef we want to show

    def setRootNode(self, node_ref: NodeRef):
        self.beginResetModel()
        self._root_node = node_ref
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        # Only the top level (invalid parent) has rows in this view
        if parent.isValid() or not self._source_model or not self._root_node:
            return 0
        return len(self._source_model.attributes(self._root_node))

    def parent(self, child: QModelIndex = QModelIndex()) -> QModelIndex:
        # Crucial: Must accept 'child' and return QModelIndex() for a flat list
        return QModelIndex()

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row, column)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and self._root_node:
            attrs = self._source_model.attributes(self._root_node)
            attr = attrs[index.row()]
            return attr._name if index.column() == 0 else self._source_model.attributeData(attr)
        return None
