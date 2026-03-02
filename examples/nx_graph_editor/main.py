# A simple example application demonstrating the use of QDAGView for building and evaluating a dataflow graph.
import sys
from typing import List

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *


import networkx as nx

from qdagview2.models.nx_graph_model import NXGraphModel
from qdagview2.models.graph_references import NodeRef, LinkRef, OutletRef, InletRef
from qdagview2.models.graph_selection_model import GraphSelectionModel
from qdagview2.views.graph_view import GraphView
from qdagview2.views.delegates.graph_delegate import GraphDelegate

from qdagview2.proxy_itemmodels.attributes_proxy_itemmodel import AttributesProxyItemModel

class NXNodeInspector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Node Inspector")
        self.setGeometry(200, 200, 300, 200)

        layout = QVBoxLayout(self)
        self.label = QLabel("Select a node to see details", self)
        layout.addWidget(self.label)
        add_attr_button = QPushButton("Add Attribute", self)
        add_attr_button.clicked.connect(self.addAttribute)
        layout.addWidget(add_attr_button)

        self.setLayout(layout)

        self._model: NXGraphModel|None = None
        self._attributes_proxy_model: AttributesProxyItemModel|None = None
        self._model_connections = []
        self._selection_model: GraphSelectionModel|None = None

        attributes_list_view = QListView(self)
        attributes_list_view.setModel(self._attributes_proxy_model)
        layout.addWidget(attributes_list_view)

    def setModel(self, model:NXGraphModel):
        if self._model is not None:
            for signal, slot in self._model_connections:
                signal.disconnect(slot)
            self._model_connections.clear()
            self._model = None

        if model is not None:
            self._model_connections = [
                (model.attributesInserted, self.updateDetails),
                (model.attributesRemoved, self.updateDetails),
                (model.attributesDataChanged, self.updateDetails)
            ]
            self._model = model

    def update_attribute_list(self):
        node = None
        if self._selection_model is not None:
            current_ref = self._selection_model.currentIndex()
            if isinstance(current_ref, NodeRef):
                node = current_ref
        self._attributes_proxy_model.setSourceModel(model, node)

    def setSelectionModel(self, selection_model:GraphSelectionModel):
        self._selection_model = selection_model
        self._selection_model.selectionChanged.connect(self.updateDetails)

    def addAttribute(self):
        if self._model is None or self._selection_model is None:
            QMessageBox.warning(self, "No Model or Selection", "Please set a model and selection model before adding attributes.")
            return
        selected_refs = self._selection_model.selectedIndexes()
        if not selected_refs:
            QMessageBox.warning(self, "No Selection", "Please select a node to add an attribute.")
            return
        
        for node_ref in filter(lambda ref: isinstance(ref, NodeRef), selected_refs):
            self._model.addAttribute(node_ref)
        
        self.updateDetails()

    def updateDetails(self):
        if self._model is None or self._selection_model is None:
            self.label.setText("No model or selection model set")
            return
        selected_refs = self._selection_model.selectedIndexes()
        if not selected_refs:
            self.label.setText("Select a node to see details")
            return
        
        details = []
        for node_ref in filter(lambda ref: isinstance(ref, NodeRef), selected_refs):
            attributes = self._model.attributes(node_ref)
            for attribute in attributes:
                name = attribute._name
                value = self._model.attributeData(attribute)
                details.append(f"{name}: {value}")

        self.label.setText("\n".join(details))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NetworkX Graph View")
        self.setGeometry(100, 100, 800, 600)
    
        # setup toolbar
        self.toolbar = QMenuBar(self)
        add_action = self.toolbar.addAction("Add Node")
        add_action.triggered.connect(self.appendNode)
        remove_action = self.toolbar.addAction("Remove Node")
        remove_action.triggered.connect(self.removeSelectedItems)
        self.toolbar.setNativeMenuBar(False)

        # setup model controller
        self.graph_model = NXGraphModel(parent=self)

        # setup selection controller
        self.graph_selection_model = GraphSelectionModel(parent=self)
        self.graph_selection_model.setGraphModel(self.graph_model)

        # # setup graph view
        self.graphview1 = GraphView(parent=self, delegate=GraphDelegate())
        self.graphview1.setModel(self.graph_model)
        self.graphview1.setSelectionModel(self.graph_selection_model)

        # setup node inspector
        self.node_inspector = NXNodeInspector(parent=self)
        self.node_inspector.setModel(self.graph_model)
        self.node_inspector.setSelectionModel(self.graph_selection_model)

        # setup layout
        layout = QHBoxLayout(self)
        layout.setMenuBar(self.toolbar)
        layout.addWidget(self.graphview1)
        layout.addWidget(self.node_inspector)
        self.setLayout(layout)


    def appendNode(self):
        new_node_ref = self.graph_model.addNode()

    def removeSelectedItems(self):
        selected_refs = self.graph_selection_model.selectedIndexes()
        self.graph_model.remove_batch(selected_refs)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
