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

from qdagview2.proxy_itemmodels.nodes_proxy_itemmodel import NodesProxyItemModel
from qdagview2.proxy_itemmodels.links_proxy_itemmodel import LinksProxyItemModel
from qdagview2.proxy_itemmodels.attributes_proxy_itemmodel import AttributesProxyItemModel


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NetworkX Graph View")
        self.setGeometry(100, 100, 800, 600)

        layout = QHBoxLayout(self)
        
        # setup toolbar
        self.toolbar = QMenuBar(self)
        add_action = self.toolbar.addAction("Add Node")
        add_action.triggered.connect(self.appendNode)
        remove_action = self.toolbar.addAction("Remove Node")
        remove_action.triggered.connect(self.removeSelectedItems)
        self.toolbar.setNativeMenuBar(False)
        layout.setMenuBar(self.toolbar)

        # setup model controller
        self.graph_model = NXGraphModel(parent=self)

        # setup selection controller
        self.graph_selection_model = GraphSelectionModel(parent=self)
        self.graph_selection_model.setGraphModel(self.graph_model)

        # # setup graph view
        self.graphview1 = GraphView(parent=self, delegate=GraphDelegate())
        self.graphview1.setModel(self.graph_model)
        self.graphview1.setSelectionModel(self.graph_selection_model)
        layout.addWidget(self.graphview1)

        # setup node list
        self.nodes_proxy_model = NodesProxyItemModel(parent=self)
        self.nodes_proxy_model.setSourceModel(self.graph_model)
        self.node_list_view = QTableView(self)
        self.node_list_view.setFixedWidth(180)
        self.node_list_view.setModel(self.nodes_proxy_model)
        layout.addWidget(self.node_list_view)

        # # setup link list
        # self.links_proxy_model = LinksProxyItemModel(parent=self)
        # self.links_proxy_model.setSourceModel(self.graph_model)
        # self.link_list_view = QTableView(self)
        # self.link_list_view.setFixedWidth(180)
        # self.link_list_view.setModel(self.links_proxy_model)

        # # setup attribute list
        # self.attributes_proxy_model = AttributesProxyItemModel(parent=self)
        # self.attributes_proxy_model.setSourceModel(self.graph_model)
        # self.attribute_list_view = QTreeView(self)
        # self.attribute_list_view.setFixedWidth(180)
        # self.attribute_list_view.setModel(self.attributes_proxy_model)

        # setup layout
        
        
        # layout.addWidget(self.attribute_list_view)
        
        # layout.addWidget(self.link_list_view)
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
