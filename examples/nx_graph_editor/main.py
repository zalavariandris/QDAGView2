# A simple example application demonstrating the use of QDAGView for building and evaluating a dataflow graph.
import sys
from typing import List

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *


import networkx as nx

from qdagview2.models.nx_graph_model import NXGraphModel
from qdagview2.models.graph_selection_model import GraphSelectionModel
from qdagview2.views.graph_view import GraphView
from qdagview2.views.delegates.graph_delegate import GraphDelegate


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
        self.graph_model.nodesInserted.connect(self.update_label)
        self.graph_model.inletsInserted.connect(self.update_label)
        self.graph_model.outletsInserted.connect(self.update_label)
        self.graph_model.linksInserted.connect(self.update_label)
        self.graph_model.nodesRemoved.connect(self.update_label)
        self.graph_model.inletsRemoved.connect(self.update_label)
        self.graph_model.outletsRemoved.connect(self.update_label)
        self.graph_model.linksRemoved.connect(self.update_label)

        # setup selection controller
        self.graph_selection_model = GraphSelectionModel(parent=self)
        self.graph_selection_model.setGraphModel(self.graph_model)
        self.graph_selection_model.currentChanged.connect(self.update_label)
        self.graph_selection_model.selectionChanged.connect(self.update_label)
        self.graph_selection_model.selectionChanged.connect(self.onSelectionChanged)

        # log signals
        self.graph_model.nodesAboutToBeInserted.connect(lambda node_refs: self.appendLog(f"Nodes about to be inserted: {node_refs}"))
        self.graph_model.nodesInserted.connect(lambda node_refs: self.appendLog(f"Nodes inserted: {node_refs}"))
        self.graph_model.inletsAboutToBeInserted.connect(lambda inlet_refs: self.appendLog(f"Inlets about to be inserted: {inlet_refs}"))
        self.graph_model.linksInserted.connect(lambda link_refs: self.appendLog(f"Links inserted: {link_refs}"))
        self.graph_model.nodesAboutToBeRemoved.connect(lambda node_refs: self.appendLog(f"Nodes about to be removed: {node_refs}"))
        self.graph_model.linksAboutToBeRemoved.connect(lambda link_refs: self.appendLog(f"Links about to be removed: {link_refs}"))
        self.graph_model.nodesRemoved.connect(lambda node_refs: self.appendLog(f"Nodes removed: {node_refs}"))
        self.graph_model.linksRemoved.connect(lambda link_refs: self.appendLog(f"Links removed: {link_refs}"))

        self.graph_selection_model.selectionChanged.connect(lambda selected, deselected: self.appendLog(f"Selection changed. Selected: {selected}, Deselected: {deselected}"))
        self.graph_selection_model.currentChanged.connect(lambda current, previous: self.appendLog(f"Current changed: {current}, Previous: {previous}"))

        # # setup graph view
        self.graphview1 = GraphView(parent=self, delegate=GraphDelegate())
        self.graphview1.setModel(self.graph_model)
        self.graphview1.setSelectionModel(self.graph_selection_model)
        self.graphview2 = GraphView(parent=self, delegate=GraphDelegate())
        self.graphview2.setModel(self.graph_model)
        self.graphview2.setSelectionModel(self.graph_selection_model)

        # label
        self.label = QLabel("Graph View")
        self.log = QPlainTextEdit("Log:")
        self.log.setReadOnly(True)

        # setup layout
        layout = QHBoxLayout(self)
        layout.setMenuBar(self.toolbar)
        layout.addWidget(self.graphview1)
        layout.addWidget(self.graphview2)
        layout.addWidget(self.label)
        layout.addWidget(self.log)
        self.setLayout(layout)

        # init
        self.update_label()

    def appendLog(self, message:str):
        self.log.appendPlainText(f"Log: {message}")

    def onSelectionChanged(self, selected, deselected):
        print("Selection changed:")
        print("- Selected:", selected)
        print("- Deselected:", deselected)
        print("- Selection:", self.graph_selection_model.selectedIndexes())
        print("- Current:", self.graph_selection_model.currentIndex())

    def update_label(self):
        print("Updating label...")
        node_count = self.graph_model.nodeCount()
        link_count = self.graph_model.linkCount()
        node_list = ""
        for n in self.graph_model.nodes():
            inlet_attributes = [self.graph_model.attributes(i) for i in self.graph_model.inlets(n)]
            outlet_attributes = [self.graph_model.attributes(o) for o in self.graph_model.outlets(n)]

            inlets =  [self.graph_model.attributeData(a, role=Qt.ItemDataRole.DisplayRole) for attrs in inlet_attributes for a in attrs]
            outlets = [self.graph_model.attributeData(a, role=Qt.ItemDataRole.DisplayRole) for attrs in outlet_attributes for a in attrs]

            is_selected = self.graph_selection_model.isSelected(n)

            node_list += f"- [{'x' if is_selected else ' '}] {n} (Inlets: {', '.join(inlets)}, Outlets: {', '.join(outlets)})\n"
        link_list = ""
        for link in self.graph_model.links():
            source_port = self.graph_model.linkSource(link)
            target_port = self.graph_model.linkTarget(link)
            is_selected = self.graph_selection_model.isSelected(link)
            link_list += f"- [{'x' if is_selected else ' '}] {source_port} -> {target_port}\n"

        from textwrap import dedent
        self.label.setText(dedent(f"""
Nodes: {node_count}
{node_list}
Links: {link_count}
{link_list}
        """))


    def appendNode(self):
        new_node_ref = self.graph_model.addNode()

    def removeSelectedItems(self):
        selected_refs = self.graph_selection_model.selectedIndexes()
        self.graph_model.remove_batch(selected_refs)

        # for item in selected_items:
        #     match item:
        #         case QGraphicsWidget() if isinstance(item, QGraphicsWidget):
        #             self.graphview._widget_manager.removeWidget(item)
        #         case _:
        #             print(f"Unknown item type: {type(item)}")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())