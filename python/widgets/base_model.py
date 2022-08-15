import sgtk
from sgtk.platform.qt import QtCore, QtGui
from .item_schemas import RowSchema

logger = sgtk.platform.get_logger(__name__)


class MultiModel(QtCore.QAbstractItemModel):
    def __init__(self, data=None, parent=None):
        super().__init__()

        self.main_ui = parent

        # self.rootItem will specify your headlines
        # TODO: pass your tree item in
        self.rootItem = RowSchema(schema="asset_item_schema")

        # TODO: make this work with lists of lists of strings
        if data:
            self.setupModelData(data, self.rootItem)

        logger.debug("was able to set up the Model!! {}".format(data))

        self.primary_roots = {}

    def columnCount(self, parent=None):
        if not parent:
            parent = self.rootItem
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    # def setData(self, index, value, role=None):
    #     item = index.internalPointer()
    #     item.set_data(index.column(), value)

    def data(self, index, role):

        try:

            if not index.isValid():
                return None

            if role not in [
                QtCore.Qt.DisplayRole,
                QtCore.Qt.UserRole,
                QtCore.Qt.DecorationRole,
            ]:
                return None
            item = index.internalPointer()
            if role == QtCore.Qt.DecorationRole:
                icon = item.column_schema[index.column()].get("icon")
                if icon:
                    return QtGui.QPixmap(self.main_ui.icon_path(icon))
            if role == QtCore.Qt.UserRole:
                # used to do simple
                return item.row()

            else:
                return item.data(index.column())
        except:
            import traceback

            logger.error(traceback.format_exc())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return (
            QtCore.Qt.ItemIsEnabled
            | QtCore.Qt.ItemIsSelectable
            | QtCore.Qt.ItemIsEditable
        )

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if hasattr(self.rootItem, "header_data"):
                return self.rootItem.header_data(section)
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=None):
        # if not parent:
        #     parent = self.rootItem
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def refresh(self):
        self.layoutAboutToBeChanged.emit()
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        self.layoutChanged.emit()

    def add_row(self, data_item):
        if data_item.get("asset_name"):
            if not self.primary_roots.get(data_item["asset_name"]):
                asset_item = RowSchema(
                    data=data_item,
                    parent=self.rootItem,
                    schema="asset_item_schema",
                    primary=True,
                )
                self.primary_roots[data_item["asset_name"]] = asset_item
            sync_item = RowSchema(
                data=data_item,
                parent=self.primary_roots[data_item["asset_name"]],
                schema="sync_item_schema",
            )
            self.refresh()

        # lines is our list

    def item(self, index):
        if not index.isValid():
            return self.rootItem
        else:
            return index.internalPointer()

    def setupModelData(self, data, parent):

        for list_item in data:
            self.add_row(list_item)
