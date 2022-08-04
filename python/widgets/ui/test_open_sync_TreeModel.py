import sys
import os
from PyQt5 import QtCore
from PyQt5.QtWidgets import QPushButton, QWidget, QHBoxLayout, QVBoxLayout,QApplication, QTreeView
from PyQt5.QtGui import QPixmap


class TreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

        

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
        
        #this seem obsolete
    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0

class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, data, parent=None):
        super(TreeModel, self).__init__(parent)

        fields = self.get_headlines(data)

        self.rootItem = TreeItem(fields)
        #self.rootItem = TreeItem(data[0])
        
        
        self.setupModelData(data, self.rootItem)

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    # def handle_case_we_wish_to_hide(item, handler):
    #     case = handler.does_make_the_case(item)

    def get_headlines(data: dict) -> list:
            """ Will sort through first entry of the list of dictionaries
            and retrieve all the keys. These will be used as headers
            in the tree view
            
            Args:
                data (dict): the dictionary we want to parse to populate the tree view
                
            Returns:
                list: strings to use as headers
            """
            
            headlines = list(data[0].keys())
            headlines.remove('parent')
            
            return headlines

    #this is the logic that should be in setupModelData most likely
    def some_method(data: dict):
        coloumn = 0
        row = 0
        parents = []
        for row, d in enumerate(data):
            
            
            if d.get('parent') == None:
                #assign row number here
                
                row = row
                parent = QtCore.QModelIndex()
                self.index()
                parents.append(d['name'])
                
                #print('this is coloumn', column)
                #print('this is row', row)
        
        
            
        
        while parents:
            print('entering while loop')
            children = []
            
            for parent in parents:
                print(parent, 'this is parent')
                for d in data:
                    if d['parent'] == parent:
                        
                        print(d['name'], 'this is child and my parent is', d['parent'])
                                
            
            column += 1
            parents = []

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
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
    def setupModelData(self, lines, parent):
        parents = [parent]
        indentations = [0]

        number = 0
        # as long as number is less than length of our list
        while number < len(lines):
            
            position = 0 #init counter
            
            lineData = lines[number]

            while position < len(lineData):
                #figure out the character length of entry
                if lines[number][position] != b' ':
                    break
                position += 1
                #"IceCream"

            if lineData:
                # Read the column data from the rest of the line.
                # columnData = [s for s in lineData.split('\t') if s]
                columnData = lineData

                # if position > indentations[-1]:
                    
                #     # The last child of the current parent is now the new
                #     # parent unless the current parent has no children.

                #     if parents[-1].childCount() > 0:
                #         parents.append(parents[-1].child(parents[-1].childCount() - 1))
                #         indentations.append(position)

                # else:
                #     while position < indentations[-1] and len(parents) > 0:
                #         parents.pop()
                #         indentations.pop()

                # Append a new item to the current parent's list of children.


                # # approach for a list of list of strings...
                # item = TreeItem(columnData, parents[-1])
                # parents[-1].appendChild(item)

                # # define rule that we extract/apply children
                # if columnData[0] == "1":
                #     child_item = TreeItem(['this', 'is a', 'child'], item)
                #     item.appendChild(child_item)

                # # approach for a list of list of strings...
                item = TreeItem(columnData, parents[-1])
                parents[-1].appendChild(item)

                # define rule that we extract/apply children
                if columnData[0] == "1":
                    child_item = TreeItem(['this', 'is a', 'child'], item)
                    item.appendChild(child_item)

            number += 1

class test_class(QWidget):
    
    def __init__(self, data=None) -> None:
        super().__init__()
        self.data = data

        self.master_layout = QVBoxLayout()
        self.setLayout(self.master_layout)

        self.model = TreeModel(self.data)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.expandAll()

        self.master_layout.addWidget(self.tree_view)

        self.render_to_image()

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
                        {
                            'name': 'asset1',
                            'status' : '3/7 synced',
                            'description' : 'asset of a kind',
                            'detail': 'path to file on disk',
                            'parent' : None
                            
                            

                        },
                        {
                            'name': 'asset2',
                            'status' : 'all files synced',
                            'description': 'another asset of a kind',
                            'detail' : 'path to file on disk',
                            'parent': None
                        },
                        {
                            'name': 'asset3',
                            'status' : '5/5 synced',
                            'detail' : 'path to file on disk',
                            'description' : 'psd file of asset1',
                            'parent': 'asset1'
                        },
                        {
                            'name': 'asset4',
                            'status' : '5/5 synced',
                            'detail' : 'path to file on disk',
                            'description': 'maya file of asset 2',
                            'parent': ' asset2'
                            
                        }
                    ]
  

        self.run()
        
    def run(self):
        app = QApplication(sys.argv)
        ui = test_class(self.data)
        sys.exit()

run_application().run()

