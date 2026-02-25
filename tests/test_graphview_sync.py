
from qdagview2.models.nx_graph_model import NXGraphModel

from qdagview2.views.graph_view import GraphView
from qdagview2.views.widgets.node_widget import NodeWidget
from qdagview2.views.widgets.link_widget import LinkWidgetStraight as LinkWidget



# Pytest fixture for QApplication
import pytest
from qtpy.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

# Use the fixture in the test

def get_widget_counts(view, NodeWidget, LinkWidget):
    node_widgets = [w for w in view._widget_manager.widgets() if isinstance(w, NodeWidget)]
    link_widgets = [w for w in view._widget_manager.widgets() if isinstance(w, LinkWidget)]
    return len(node_widgets), len(link_widgets)


def test_node_addition_removal(qapp):
    from qdagview2.views.graph_view import GraphView
    from qdagview2.views.widgets.node_widget import NodeWidget
    from qdagview2.views.widgets.link_widget import LinkWidgetStraight as LinkWidget

    graph = NXGraphModel()
    view = GraphView()
    view.setModel(graph)

    # Add nodes
    n1 = graph.addNode()
    n2 = graph.addNode()
    node_count, link_count = get_widget_counts(view, NodeWidget, LinkWidget)
    assert node_count == 2, f"Expected 2 node widgets after add, got {node_count}"
    assert link_count == 0, f"Expected 0 link widgets after add, got {link_count}"

    # Remove a node
    graph.removeNode(n1)
    node_count, link_count = get_widget_counts(view, NodeWidget, LinkWidget)
    assert node_count == 1, f"Expected 1 node widget after removal, got {node_count}"
    assert link_count == 0, f"Expected 0 link widgets after node removal, got {link_count}"

def test_link_addition(qapp):
    from qdagview2.views.graph_view import GraphView
    from qdagview2.views.widgets.node_widget import NodeWidget
    from qdagview2.views.widgets.link_widget import LinkWidgetStraight as LinkWidget

    graph = NXGraphModel()
    view = GraphView()
    view.setModel(graph)

    n1 = graph.addNode()
    n2 = graph.addNode()

    # Add link
    l1 = graph.addLink(graph.outlets(n1)[0], graph.inlets(n2)[0])

    node_count, link_count = get_widget_counts(view, NodeWidget, LinkWidget)
    assert node_count == 2, f"Expected 2 node widgets after link add, got {node_count}"
    assert link_count == 1, f"Expected 1 link widget after link add, got {link_count}"

    # RemoveLink
    graph.removeLink(l1)
    node_count, link_count = get_widget_counts(view, NodeWidget, LinkWidget)
    assert link_count == 0, f"Expected 0 link widgets after link removal, got {link_count}"

@pytest.fixture(scope="session")
def simple_graph():
    graph = NXGraphModel()
    view = GraphView()
    view.setModel(graph)

    n1 = graph.addNode()
    n2 = graph.addNode()
    n3 = graph.addNode()
    l1 = graph.addLink(graph.outlets(n1)[0], graph.inlets(n2)[0])
    l2 = graph.addLink(graph.outlets(n2)[0], graph.inlets(n3)[0])

    yield graph, view, [n1, n2, n3], [l1, l2]

def test_links_removed_with_node(simple_graph,qapp):
    from qdagview2.views.graph_view import GraphView
    from qdagview2.views.widgets.node_widget import NodeWidget
    from qdagview2.views.widgets.link_widget import LinkWidgetStraight as LinkWidget

    # setup
    graph = NXGraphModel()
    view = GraphView()
    view.setModel(graph)

    n1 = graph.addNode()
    n2 = graph.addNode()
    n3 = graph.addNode()
    l1 = graph.addLink(graph.outlets(n1)[0], graph.inlets(n2)[0])
    l2 = graph.addLink(graph.outlets(n2)[0], graph.inlets(n3)[0])

    # Remove node in the middle
    graph.removeNode(n2)
    _, link_count = get_widget_counts(view, NodeWidget, LinkWidget)
    assert link_count == 0, f"Expected 0 link widgets after removing node with links, got {link_count}"

