import sgtk
from sgtk.platform.qt import QtCore, QtGui
from .item_schemas import ItemSchema

logger = sgtk.platform.get_logger(__name__)


class MultiModel(QtCore.QAbstractItemModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)

        #self.rootItem will specify your headlines
        # TODO: pass your tree item in
        self.rootItem = ItemSchema(data=data[0], schema='asset_item_schema')
        
        # TODO: make this work with lists of lists of strings
        self.setupModelData(data, self.rootItem)

        logger.debug('was able to set up the Model!!')


    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def setData(self, index, value, role=None):
        item = index.internalPointer()
        item.set_data(index.column(), value)

    def data(self, index, role):
        if not index.isValid():
            return None

        if role not in [QtCore.Qt.DisplayRole, QtCore.Qt.UserRole]:
            return None

        item = index.internalPointer()

        if role == QtCore.Qt.UserRole:
            return item.row()
        else:
            return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

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

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()
    
        #lines is our list
    def setupModelData(self, data, parent):

        for list_item in data:
            if list_item.get("asset"):
                asset_item = ItemSchema(data=list_item, parent=self.rootItem, schema='asset_item_schema', primary=True)
                sync_item = ItemSchema(data=list_item, parent=asset_item, schema='sync_item_schema') 