from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import List, Optional

from qtpy.QtCore import QAbstractItemModel, QModelIndex, Qt
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


@dataclass
class TreeItem:
    values: List[str]
    parent: Optional["TreeItem"] = None
    children: List["TreeItem"] = field(default_factory=list)

    def child(self, row: int) -> Optional["TreeItem"]:
        if 0 <= row < len(self.children):
            return self.children[row]
        return None

    def child_count(self) -> int:
        return len(self.children)

    def column_count(self) -> int:
        return len(self.values)

    def row(self) -> int:
        if self.parent is None:
            return 0
        return self.parent.children.index(self)

    def insert_child(self, row: int, item: "TreeItem") -> None:
        item.parent = self
        self.children.insert(row, item)

    def remove_child(self, row: int) -> bool:
        if 0 <= row < len(self.children):
            child = self.children.pop(row)
            child.parent = None
            return True
        return False

    def insert_column(self, column: int, default_value: str = "") -> None:
        self.values.insert(column, default_value)
        for child in self.children:
            child.insert_column(column, default_value)

    def remove_column(self, column: int) -> None:
        if 0 <= column < len(self.values):
            self.values.pop(column)
        for child in self.children:
            child.remove_column(column)


class TreeModel(QAbstractItemModel):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._headers: List[str] = ["Column 1"]
        self._root = TreeItem(values=["Root"])
        self._seed()

    def _seed(self) -> None:
        a = TreeItem(["A"], self._root)
        a.children.append(TreeItem(["A.1"], a))
        a.children.append(TreeItem(["A.2"], a))

        b = TreeItem(["B"], self._root)
        b.children.append(TreeItem(["B.1"], b))

        self._root.children.extend([a, b])

    def _item_from_index(self, index: QModelIndex) -> TreeItem:
        if index.isValid():
            return index.internalPointer()  # type: ignore[return-value]
        return self._root

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item = self._item_from_index(parent)
        child_item = parent_item.child(row)
        if child_item is None:
            return QModelIndex()

        return self.createIndex(row, column, child_item)

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        child_item = self._item_from_index(index)
        parent_item = child_item.parent

        if parent_item is None or parent_item is self._root:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.column() > 0:
            return 0

        parent_item = self._item_from_index(parent)
        return parent_item.child_count()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            item = self._item_from_index(parent)
            return item.column_count()
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None

        item = self._item_from_index(index)
        if 0 <= index.column() < len(item.values):
            return item.values[index.column()]
        return ""

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole:
            return False

        item = self._item_from_index(index)
        if not (0 <= index.column() < len(item.values)):
            return False

        item.values[index.column()] = str(value)
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role in (Qt.DisplayRole, Qt.EditRole):
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def setHeaderData(
        self,
        section: int,
        orientation: Qt.Orientation,
        value,
        role: int = Qt.EditRole,
    ) -> bool:
        if orientation != Qt.Horizontal or role != Qt.EditRole:
            return False
        if not (0 <= section < len(self._headers)):
            return False

        self._headers[section] = str(value)
        self.headerDataChanged.emit(orientation, section, section)
        return True

    def add_child_item(self, parent_index: QModelIndex) -> QModelIndex:
        parent_item = self._item_from_index(parent_index)
        insert_row = parent_item.child_count()

        self.beginInsertRows(parent_index, insert_row, insert_row)
        new_values = [f"Item {insert_row + 1}"] + ["" for _ in range(self.columnCount() - 1)]
        new_item = TreeItem(values=new_values, parent=parent_item)
        parent_item.insert_child(insert_row, new_item)
        self.endInsertRows()

        return self.index(insert_row, 0, parent_index)

    def remove_item(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False

        item = self._item_from_index(index)
        parent_item = item.parent
        if parent_item is None:
            return False

        parent_index = QModelIndex() if parent_item is self._root else self.createIndex(parent_item.row(), 0, parent_item)
        row = item.row()

        self.beginRemoveRows(parent_index, row, row)
        ok = parent_item.remove_child(row)
        self.endRemoveRows()
        return ok

    def add_column(self, header_name: str) -> int:
        new_column = len(self._headers)
        self.beginInsertColumns(QModelIndex(), new_column, new_column)
        self._headers.append(header_name)
        self._root.insert_column(new_column, "")
        self.endInsertColumns()
        return new_column

    def remove_column(self, column: int) -> bool:
        if len(self._headers) <= 1:
            return False
        if not (0 <= column < len(self._headers)):
            return False

        self.beginRemoveColumns(QModelIndex(), column, column)
        self._headers.pop(column)
        self._root.remove_column(column)
        self.endRemoveColumns()
        return True


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Tree Model Editor")
        self.resize(960, 600)

        self.model = TreeModel(self)
        self.view = QTreeView(self)
        self.view.setModel(self.model)
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.view.setEditTriggers(
            QTreeView.DoubleClicked
            | QTreeView.SelectedClicked
            | QTreeView.EditKeyPressed
        )
        self.view.header().setSectionResizeMode(QHeaderView.Stretch)
        self.view.selectionModel().currentChanged.connect(self.sync_subtree_root)

        self.subtree_view = QTreeView(self)
        self.subtree_view.setModel(self.model)
        self.subtree_view.setAlternatingRowColors(True)
        self.subtree_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.subtree_view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.subtree_view.setEditTriggers(
            QTreeView.DoubleClicked
            | QTreeView.SelectedClicked
            | QTreeView.EditKeyPressed
        )
        self.subtree_view.header().setSectionResizeMode(QHeaderView.Stretch)
        self.view.header().sectionResized.connect(self.sync_column_width_to_subtree)

        add_root_btn = QPushButton("Add Root Item")
        add_child_btn = QPushButton("Add Child Item")
        remove_btn = QPushButton("Remove Selected")

        add_root_btn.clicked.connect(self.add_root_item)
        add_child_btn.clicked.connect(self.add_child_item)
        remove_btn.clicked.connect(self.remove_selected_items)

        add_column_btn = QPushButton("Add Column")
        add_column_btn.clicked.connect(self.add_column)
        remove_column_btn = QPushButton("Remove Column")
        remove_column_btn.clicked.connect(self.remove_column)
        rename_column_btn = QPushButton("Rename Current Column")
        rename_column_btn.clicked.connect(self.rename_current_column)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.addWidget(QLabel("Items"))
        controls_layout.addWidget(add_root_btn)
        controls_layout.addWidget(add_child_btn)
        controls_layout.addWidget(remove_btn)
        controls_layout.addSpacing(12)
        controls_layout.addWidget(QLabel("Columns"))
        controls_layout.addWidget(add_column_btn)
        controls_layout.addWidget(remove_column_btn)
        controls_layout.addWidget(rename_column_btn)
        controls_layout.addSpacing(12)
        controls_layout.addStretch(1)

        central = QWidget()
        layout = QHBoxLayout(central)
        views = QWidget()
        views_layout = QVBoxLayout(views)
        views_layout.addWidget(QLabel("Main Tree"))
        views_layout.addWidget(self.view, 2)
        views_layout.addWidget(QLabel("Current Subtree"))
        views_layout.addWidget(self.subtree_view, 1)

        layout.addWidget(views, 3)
        layout.addWidget(controls, 1)
        self.setCentralWidget(central)

        self.view.expandAll()
        self.subtree_view.expandAll()

    def selected_index(self) -> QModelIndex:
        index = self.view.currentIndex()
        if index.isValid():
            return index
        return QModelIndex()

    def sync_subtree_root(self, current: QModelIndex, previous: QModelIndex) -> None:
        del previous
        if not current.isValid():
            self.subtree_view.setRootIndex(QModelIndex())
            return

        root = current.sibling(current.row(), 0)
        self.subtree_view.setRootIndex(root)
        self.subtree_view.expandAll()

    def sync_column_width_to_subtree(self, logical_index: int, old_size: int, new_size: int) -> None:
        del old_size
        self.subtree_view.header().resizeSection(logical_index, new_size)

    def add_root_item(self) -> None:
        index = self.model.add_child_item(QModelIndex())
        self.view.expandAll()
        self.view.setCurrentIndex(index)

    def add_child_item(self) -> None:
        parent_index = self.selected_index()
        if parent_index.isValid():
            parent_index = parent_index.sibling(parent_index.row(), 0)
        self.model.add_child_item(parent_index)
        self.view.expand(parent_index)

    def remove_selected_items(self) -> None:
        selection_model = self.view.selectionModel()
        selected_indexes = selection_model.selectedIndexes()
        if not selected_indexes:
            QMessageBox.information(self, "Remove Item", "Select one or more items to remove.")
            return

        row_roots_by_item_id = {}
        for index in selected_indexes:
            row_root = index.sibling(index.row(), 0)
            row_roots_by_item_id[id(row_root.internalPointer())] = row_root
        selected_rows = list(row_roots_by_item_id.values())
        selected_item_ids = set(row_roots_by_item_id.keys())

        def has_selected_ancestor(index: QModelIndex) -> bool:
            parent = index.parent()
            while parent.isValid():
                if id(parent.internalPointer()) in selected_item_ids:
                    return True
                parent = parent.parent()
            return False

        roots = [index for index in selected_rows if not has_selected_ancestor(index)]

        def depth(index: QModelIndex) -> int:
            d = 0
            parent = index.parent()
            while parent.isValid():
                d += 1
                parent = parent.parent()
            return d

        roots.sort(key=lambda index: (depth(index), index.row()), reverse=True)
        for index in roots:
            self.model.remove_item(index)

    def add_column(self) -> None:
        default_name = f"Column {self.model.columnCount() + 1}"
        header, ok = QInputDialog.getText(
            self,
            "Add Column",
            "New column name:",
            text=default_name,
        )
        if not ok:
            return

        header = header.strip() or default_name
        new_col = self.model.add_column(header)
        self.view.header().setSectionResizeMode(new_col, QHeaderView.Stretch)
        self.subtree_view.header().setSectionResizeMode(new_col, QHeaderView.Stretch)

    def remove_column(self) -> None:
        if self.model.columnCount() <= 1:
            QMessageBox.warning(self, "Remove Column", "At least one column must remain.")
            return

        max_index = self.model.columnCount() - 1
        value, ok = QInputDialog.getInt(
            self,
            "Remove Column",
            "Column index to remove (0-based):",
            value=max_index,
            min=0,
            max=max_index,
        )
        if not ok:
            return

        removed = self.model.remove_column(value)
        if not removed:
            QMessageBox.warning(self, "Remove Column", "Invalid column index.")

    def rename_current_column(self) -> None:
        current = self.view.currentIndex()
        if not current.isValid():
            QMessageBox.information(self, "Rename Column", "Set a current cell first.")
            return

        column = current.column()
        old_name = self.model.headerData(column, Qt.Horizontal, Qt.DisplayRole) or f"Column {column + 1}"
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Current Column",
            f"New name for column {column}:",
            text=str(old_name),
        )
        if not ok:
            return

        new_name = new_name.strip()
        if not new_name:
            QMessageBox.warning(self, "Rename Column", "Column name cannot be empty.")
            return

        self.model.setHeaderData(column, Qt.Horizontal, new_name, Qt.EditRole)


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
