import sys
import os
from PyQt5 import QtCore
from PyQt5.QtWidgets import QPushButton, QWidget, QHBoxLayout, QVBoxLayout,QApplication, QTreeView
from PyQt5.QtGui import QPixmap

class TreeItem(object):
    def __init__(self, data: dict, parent=None):
        self.parentItem = parent


        self.itemData = self.transform_data(data)
        
        #if we go the route of parents instead of childs this is not needed
        self.childItems = []

    def transform_data(self, data):
        name = data.get('name', "No name given")
        status = data.get('status', "No status")
        info = data.get('info', "No info")
        return [name, status, info, 'anotherthing']

        #we wouldn't append children as we can just look up a given parent instead
    def appendChild(self, item: object) -> None:
        self.childItems.append(item)

    def child(self, row: int) -> object():
        return self.childItems[row]

    def childCount(self) -> int:
        return len(self.childItems)

    def columnCount(self) -> int:
        return len(self.itemData)

    def data(self, column: int):
        try:
            # self.itemData = ['1', '2', '3']
            return self.itemData[int]

        except IndexError:
            return None
    
    def parent(self, index) -> object:
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

    def row(self) -> int:
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0
    
    
class TreeModel(QtCore.QAbstractItemModel):
    
    def __init__(self, data, parent=None):
        super(TreeModel, self).__init(parent)
        
        #extract the headers
        fields = self.get_headlines(data)

        self.rootItem = TreeItem(fields)
        
        
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
    
    def some_setup_method(data: dict):
        data = [
        {
        'type' : 'sync_item',
        'name': 'Ankylo_v001.psd',
        'detail' : 'path to file on disk',
        'description' : 'psd file of asset1',
        'asset': 'Ankylo'
        },
        {
        'type': 'sync_item',
        'name': 'Trex_v001.psd',
        'detail' : 'path to file on disk',
        'description': 'maya file of asset 2',
        'asset': 'Trex'
        }
        ]
        
        coloumn = 0
        row = 0
        parents = []
        for row, d in enumerate(data):
            sync_item = TreeItem(d)

            # assert meaning to make parent relationship
            if d.get('asset'):

                asset_item = TreeItem({"name": d['asset'])})
                asset_item.appendChild(sync_item)

            if d.get('project'):
                project_item = TreeItem({"project": d['project'])})
            
            else:         
            # make item no matter what
      
                self.rootItem.appendChild(sync_item)






        
    def some_method(data: dict):

        self.assets = {}
        coloumn = 0
        row = 0
        parents = []
        for row, d in enumerate(data):
            
            # make item no matter what


            if d.get('parent') != None:


                

                AssetName = SOU22_110
                name = AssetName = .split('_')
                name = name[0]
                TreeItem(d) -> name
                
                #assign row number here
                
                #craft list, grab length assign row
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
                                
            #add child to parent list and remove current parent
            column += 1
            parents = []

        
    
class TreeDelegate():
    pass
class TreeView():
    pass





data = [
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
  
    



            
    
        
        
    

        
