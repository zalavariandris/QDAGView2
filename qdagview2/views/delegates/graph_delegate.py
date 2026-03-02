from __future__ import annotations

import logging
import weakref

from qdagview2.models.abstract_graph_model import AbstractGraphModel
from qdagview2.models.graph_references import AttributeRef, NodeRef, OutletRef, InletRef, LinkRef
logger = logging.getLogger(__name__)

from typing import *

from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtWidgets import *

from qdagview2.views.widgets.node_widget import NodeWidget
from qdagview2.views.widgets.port_widget import OutletWidget, InletWidget
from qdagview2.views.widgets.link_widget import LinkWidgetStraight as LinkWidget
from qdagview2.views.widgets.cell_widget import CellWidget

if TYPE_CHECKING:
    from qdagview2.views.graph_view import GraphView


class GraphDelegate(QObject):
    portPositionChanged = Signal(object)

    ## Root widgets
    def createNodeWidget(self, parent_widget: QGraphicsScene, ref:NodeRef, graphview:'GraphView'=None) -> 'NodeWidget':
        if not isinstance(parent_widget, QGraphicsScene):
            raise TypeError("Parent widget must be a QGraphicsScene")
        # if not index.isValid():
        #     raise ValueError("Index must be valid")
        
        widget = NodeWidget()
        model = graphview._graph_model
        parent_widget.addItem(widget)
        return widget

    def destroyNodeWidget(self, parent_widget: QGraphicsScene, widget: NodeWidget):
        if not isinstance(parent_widget, QGraphicsScene):
            raise TypeError("Parent widget must be a QGraphicsScene")
        
        if not isinstance(widget, NodeWidget):
            raise TypeError("Widget must be a NodeWidget")
        
        parent_widget.removeItem(widget)

    def createLinkWidget(self, source_widget, target_widget, index: QModelIndex, graphview:'GraphView'=None) -> LinkWidget:
        """Create a link widget. Links are added directly to the scene."""
        if not isinstance(source_widget, QGraphicsItem):
            raise TypeError("source_widget must be a QGraphicsItem")
        if not isinstance(target_widget, QGraphicsItem):
            raise TypeError("target_widget must be a QGraphicsItem")
        
        scene = source_widget.scene()
        if scene is None or scene != target_widget.scene():
            raise ValueError("source_widget and target_widget must be in the same scene")

        link_widget = LinkWidget()
        scene.addItem(link_widget)  # Links are added to the scene, not to the inlet widget
        return link_widget
    
    def destroyLinkWidget(self, scene: QGraphicsScene, widget: LinkWidget):
        if not isinstance(scene, QGraphicsScene):
            raise TypeError("Scene must be a QGraphicsScene")
        if not isinstance(widget, LinkWidget):
            raise TypeError("Widget must be a LinkWidget")
                
        scene.removeItem(widget)
        # Schedule widget for deletion to prevent memory leaks
        widget.deleteLater()

    # Horizontal widgets
    def createNodeColumnWidget(self, parent_widget: NodeWidget, ref: NodeRef, col:int, graphview:'GraphView'=None) -> CellWidget:
        if not isinstance(parent_widget, NodeWidget):
            raise TypeError("Parent widget must be a NodeWidget")
        # if not index.isValid():
        #     raise ValueError("Index must be valid")

        cell = CellWidget()
        model = graphview._graph_model
        assert isinstance(model, AbstractGraphModel)
        header_data = model.nodeHeaderData(col, Qt.ItemDataRole.DisplayRole)
        data = model.nodeData(ref, col, Qt.ItemDataRole.DisplayRole)
        cell.setText(f"{header_data}: {data}")
        parent_widget.insertHeaderCell(col, cell)
        return cell
    
    def destroyNodeColumnWidget(self, parent_widget: NodeWidget, widget: CellWidget):
        if not isinstance(parent_widget, NodeWidget):
            raise TypeError("Parent widget must be a NodeWidget")
        if not isinstance(widget, CellWidget):
            raise TypeError("Widget must be a CellWidget")
        
        parent_widget.removeHeaderCell(widget)
        # Schedule widget for deletion - this automatically disconnects all signals
        widget.deleteLater()
    
    # child widgets
    def createInletWidget(self, parent_widget: InletWidget, index: InletRef, graphview:'GraphView'=None) -> InletWidget:
        if not isinstance(parent_widget, NodeWidget):
            raise TypeError("Parent widget must be a NodeWidget")
        # if not index.isValid():
        #     raise ValueError("Index must be valid")

        # get inlet position from graph controller TODO: this is a bit hacky, we should have a cleaner way to get the port position without relying on the graph controller
        graph_model = graphview._graph_model
        node_ref = graph_model.inletNode(index)
        inlets = graph_model.inlets(node_ref) # Ensure inlets are loaded for the node
        pos = inlets.index(index)
        if pos == -1:
            raise ValueError(f"Port {index} is not an inlet of node {node_ref}")
        
        widget = InletWidget()
        parent_widget.insertInlet(pos, widget)
        
        # Store the persistent index directly on the widget
        # This avoids closure issues entirely
        widget.setProperty("modelIndex", index)
        
        # Connect using a simple lambda that gets the property
        widget.scenePositionChanged.connect(
            lambda: self.portPositionChanged.emit(widget.property("modelIndex")) 
            # if widget.property("modelIndex").isValid() else None
        )
        return widget
    
    def destroyInletWidget(self, parent_widget: NodeWidget, widget: InletWidget):
        if not isinstance(parent_widget, NodeWidget):
            raise TypeError("Parent widget must be a NodeWidget")
        if not isinstance(widget, InletWidget):
            raise TypeError("Widget must be an InletWidget")
        
        parent_widget.removeInlet(widget)
        # Schedule widget for deletion - this automatically disconnects all signals
        widget.deleteLater()
    
    def createOutletWidget(self, parent_widget: NodeWidget, index: QModelIndex, graphview:'GraphView'=None) -> OutletWidget:
        if not isinstance(parent_widget, NodeWidget):
            raise TypeError("Parent widget must be a NodeWidget")
        # if not index.isValid():
        #     raise ValueError("Index must be valid")
        
        widget = OutletWidget()
        # get outlet position from graph controller TODO: this is a bit hacky, we should have a cleaner way to get the port position without relying on the graph controller
        graph_model = graphview._graph_model
        node_ref = graph_model.outletNode(index)
        outlets = graph_model.outlets(node_ref) # Ensure outlets are loaded for the node
        pos = outlets.index(index)
        if pos == -1:
            raise ValueError(f"Port {index} is not an outlet of node {node_ref}")

        parent_widget.insertOutlet(pos, widget)
        
        # Store the persistent index directly on the widget
        # This avoids closure issues entirely
        widget.setProperty("modelIndex", index)
        
        # Connect using a simple lambda that gets the property
        widget.scenePositionChanged.connect(
            lambda: self.portPositionChanged.emit(widget.property("modelIndex")) 
            # if widget.property("modelIndex").isValid() else None
        )
        return widget
    
    def destroyOutletWidget(self, parent_widget: NodeWidget, widget: OutletWidget):
        if not isinstance(parent_widget, NodeWidget):
            raise TypeError("Parent widget must be a NodeWidget")
        if not isinstance(widget, OutletWidget):
            raise TypeError("Widget must be an OutletWidget")

        parent_widget.removeOutlet(widget)
        # Schedule widget for deletion - this automatically disconnects all signals
        widget.deleteLater()
        
    def createAttributeWidget(self, parent_widget: NodeWidget|OutletWidget|InletWidget|LinkWidget, attribute: AttributeRef, graphview:'GraphView'=None) -> CellWidget:
        if not isinstance(parent_widget, (NodeWidget, OutletWidget, InletWidget, LinkWidget)):
            raise TypeError("Parent widget must be a NodeWidget, PortWidget, or LinkWidget")
        # if not index.isValid():
        #     raise ValueError("Index must be valid")

        match parent_widget:
            case NodeWidget():
                cell = CellWidget()
                owner = graphview._graph_model.attributeOwner(attribute)
                attributes = graphview._graph_model.attributes(owner)
                pos = attributes.index(attribute)
                if pos == -1:
                    raise ValueError(f"Attribute {attribute} is not an attribute of {owner}")
                parent_widget.insertSideCell(pos, cell)
                return cell
            
            case OutletWidget() | InletWidget() | LinkWidget():
                cell = CellWidget()
                owner = graphview._graph_model.attributeOwner(attribute)
                attributes = graphview._graph_model.attributes(owner)
                pos = attributes.index(attribute)
                if pos == -1:
                    raise ValueError(f"Attribute {attribute} is not an attribute of {owner}")
                parent_widget.insertCell(pos, cell)
                return cell
        
    def destroyAttributeWidget(self, parent_widget: NodeWidget|OutletWidget|InletWidget|LinkWidget, widget: CellWidget):
        if not isinstance(parent_widget, (NodeWidget, OutletWidget, InletWidget, LinkWidget)):
            raise TypeError("Parent widget must be a NodeWidget, PortWidget, or LinkWidget")
        if not isinstance(widget, CellWidget):
            raise TypeError("Widget must be a CellWidget")
        
        match parent_widget:
            case NodeWidget():
                parent_widget.removeSideCell(widget)
                widget.deleteLater()
            case OutletWidget() | InletWidget() | LinkWidget():
                parent_widget.removeCell(widget)
                widget.deleteLater()

    def setAttributeEditorData(self, editor:QWidget, controller:AbstractGraphModel , index:QModelIndex|QPersistentModelIndex):
        if isinstance(editor, QLineEdit):
            text = controller.attributeData(index, Qt.ItemDataRole.DisplayRole)
            editor.setText(text)
    
    def setModelAttributeData(self, editor:QWidget, controller:AbstractGraphModel, index:QModelIndex|QPersistentModelIndex):
        if isinstance(editor, QLineEdit):
            text = editor.text()
            controller.setAttributeData(index, text, Qt.ItemDataRole.EditRole)
        else:
            raise TypeError(f"Editor must be a QLineEdit, got {type(editor)} instead.")
