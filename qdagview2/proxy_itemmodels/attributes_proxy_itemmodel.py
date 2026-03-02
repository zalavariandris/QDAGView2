from __future__ import annotations
from typing import *

from qtpy.QtGui import *
from qtpy.QtCore import *

from qdagview2.models.graph_references import (
    NodeRef, OutletRef, InletRef, LinkRef)
from qdagview2.models.abstract_graph_model import AbstractGraphModel


class AttributesProxyItemModel(QAbstractItemModel):
    sourceModelChanged = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._source_model:AbstractGraphModel|None = None
        self._source_item:NodeRef = None
        self._connections = []

    def setSourceModel(self, source_model:AbstractGraphModel, source_item:NodeRef|OutletRef|InletRef|LinkRef):
        self._source_item = source_item
        self._source_model = source_model
        self.sourceModelChanged.emit()

        if self._source_model is not None:
            for signal, slot in self._connections:
                signal.disconnect(slot)
            self._connections = []

        if source_model is not None:
            self._connections = [
                (source_model.attributesInserted, self.onAttributesChanged),
                (source_model.attributesRemoved, self.onAttributesChanged),
                (source_model.attributesDataChanged, self.onAttributesChanged)
            ]
            for signal, slot in self._connections:
                signal.connect(slot)

    def onAttributesChanged(self, item_ref, attribute_name):
        print(f"Attributes changed for {item_ref}, attribute: {attribute_name}")
        if item_ref == self._source_item:
            self.layoutChanged.emit()

    def sourceModel(self):
        return self._source_model, self._source_item

    def rowCount(self, parent=None):
        attributes = self._source_model.attributes(self._source_item)
        return len(attributes)

    def columnCount(self, parent=None):
        return 2

    def data(self, index, role=None):
        if not index.isValid():
            return None
        attributes = self._source_model.attributes(self._source_item)
        if index.row() >= len(attributes):
            return None
        attribute_name = attributes[index.row()]
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return attribute_name
            elif index.column() == 1:
                return self._source_model.attributeData(self._source_item, attribute_name)
        return None

    def headerData(self, section, orientation, role=None):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return "Attribute"
            elif section == 1:
                return "Value"
        return None
