import sys

sys.path.append("""C:/Users/cam_admin/AppData/Local/Programs/Python/python37-32/lib/site-packages""".replace("\\", "/"))

import os
from PySide2 import QtCore
from PySide2.QtWidgets import QPushButton, QWidget, QHBoxLayout, QVBoxLayout,QApplication, QTreeView, QStyledItemDelegate, QDoubleSpinBox, QListView, QTableView
from PySide2.QtGui import QPixmap


sync_item_schema = [
    {
        "key" : "sync_filename",
        "title": "Name",
        "default": "No name",
        "delegate" : None
    },
    {
        "key" : "sync_path",
        "title": "Descr",
        "default": "No Description"
    },
    {
        "key" : "version",
        "title": "Version",
        "default": "No Description"
    },
]

asset_item_schema = [ 
    {
        "key" : "asset",
        "title": "Name",
        "default": "No name"
    },
    {
        "key" : "status",
        "title": "Descr",
        "default": "No Description"
    },
    {
        "key" : "_",
        "title": "Version",
        "default": " "
    }

]


class TreeItem(object):
    def __init__(self, data, parent=None):
        self.childItems = []
        self.data_in = data
        self.parentItem = parent
        if parent:
            parent.appendChild(self)

    @property
    def itemData(self):
        return list(self.data_in.keys())

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None
        
        #this runs in the model
    def parent(self):
        return self.parentItem

    def row(self):
        if hasattr(self, 'primary'):
            if not self.primary:
                if self.parentItem:
                    return self.parentItem.childItems.index(self) + 1

        return 0


class TreeItemSchema(TreeItem):
    def __init__(self, data, schema=None, parent=None, primary=False, **kwargs):
        self._cached_data = []
        self._col_map = [i.get('key') for i in schema]
        self.primary = primary

        # how we will render our data to the model
        self._serial_data = []
        
        if not schema:
            raise Exception("Schema-driven items require a schema to reference.")

        self.column_schema = schema

        super().__init__(data=data, parent=parent, **kwargs)

    def header_data(self, index):
        return self.column_schema[index].get('title')

    def set_data(self, index, value):
        self.data_in[self._col_map[index]] = value

    @property
    def itemData(self):
        
        self._serial_data =  []
        for item in self.column_schema:
            
            val = "n/a"
            # cerberus match against schema
            if self.data_in.get(item['key']):
                val = self.data_in[item['key']]
            elif item.get('default'):
                val = item['default']
            self._serial_data.append(val)
        return self._serial_data


class MultiDelegate(QStyledItemDelegate):
    """
    A delegate class displaying a double spin box.
    https://stackoverflow.com/questions/61663446/with-pyside2-and-qtableview-how-do-i-get-multiple-delegates-in-table-view-using
    """

    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)
        pass

    def createEditor(self, parent, option, index):
        editor = QPushButton("name", parent=parent)
        return editor

    def setEditorData(self, spinBox, index):
        pass

    def setModelData(self, spinBox, model, index):
        return True

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class DoubleSpinBoxDelegate(QStyledItemDelegate):
    """
    A delegate class displaying a double spin box.
    https://stackoverflow.com/questions/61663446/with-pyside2-and-qtableview-how-do-i-get-multiple-delegates-in-table-view-using
    """

    def __init__(self, parent=None, minimum=0.0, maximum=100.0, step=0.01):
        QStyledItemDelegate.__init__(self, parent)
        self._min = minimum
        self._max = maximum
        self._step = step

    def createEditor(self, parent, option, index):
        row_index = index.data(QtCore.Qt.UserRole)
        if row_index == 1:
            editor = QDoubleSpinBox(parent)
            editor.setMinimum(self._min)
            editor.setMaximum(self._max)
            editor.setSingleStep(self._step)
            editor.setAccelerated(True)
            editor.installEventFilter(self)
            return editor

    def setEditorData(self, spinBox, index):
        value = float(index.model().data(index, QtCore.Qt.DisplayRole))
        spinBox.setValue(value)

    def setModelData(self, spinBox, model, index):
        value = spinBox.value()
        model.setData(index, value)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)



class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, data, parent=None):
        super(TreeModel, self).__init__(parent)

        #self.rootItem will specify your headlines
        # TODO: pass your tree item in
        self.rootItem = TreeItemSchema(data=data[0], schema=asset_item_schema)
        
        # TODO: make this work with lists of lists of strings
        self.setupModelData(data, self.rootItem)

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
                asset_item = TreeItemSchema(data=list_item, parent=self.rootItem, schema=asset_item_schema, primary=True)
                sync_item = TreeItemSchema(data=list_item, parent=asset_item, schema=sync_item_schema)  


class test_class(QWidget):
    
    def __init__(self, data=None) -> None:
        super().__init__()
        self.data = data

        self.master_layout = QVBoxLayout()
        self.setLayout(self.master_layout)

        self.model = TreeModel(self.data)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setItemDelegateForColumn(1, MultiDelegate(self.tree_view))
        self.tree_view.setItemDelegateForColumn(2, DoubleSpinBoxDelegate(self.tree_view))
        self.tree_view.expandAll()

        self.list_view = QListView()
        self.list_view.setModel(self.model)

        self.table_view = QTableView()
        self.table_view.setModel(self.model)


        self.master_layout.addWidget(self.tree_view)
        self.master_layout.addWidget(self.list_view)
        self.master_layout.addWidget(self.table_view)


    def render_to_image(self, image_file_path="my_screenshot.png"):

        # define where to save the screenshot
        basepath = os.path.dirname(os.path.abspath(__file__))
        # print(basepath,'this is basepath')
        screenshot_path = os.path.join(basepath, image_file_path)
        # print(screenshot_path, 'this is screen path')
        
        # bake the ui
        self.screenshot_pixmap = QPixmap(self.size())
        self.render(self.screenshot_pixmap)

        # save to disk
        os.remove(screenshot_path)
        self.screenshot_pixmap.save(screenshot_path)



class run_application(object):
    """
    This class contains all the functionality used to generate the flipbook
    """


    def __init__(self) -> None:
        # self.data = [
        #     {"children" : ["something", "lkjsdflkjsdf"], "2_version_field_3": }
        # ]
        self.data = [
            {'asset': "Ankylo",
            "sync_filename" : "Ankylo_concept_v001.psd",
            "sync_path": "/shows/test/Ankylo_concept_v001.psd",
            "status" : "Peaceful",
            "version": 1
            },
            {'asset': "Ankylo2",
            "sync_filename" : "Ankylo2_concept_v001.psd",
            "sync_path": None,
            "status" : "Peaceful",
            "version": 1
            }
        ]
        self.run()
        
    def run(self):
        app = QApplication(sys.argv)
        ui = test_class(self.data)
        #sys.exit()
        ui.show()
        ui.render_to_image()
        app.exec_()
        

run_application().run()
