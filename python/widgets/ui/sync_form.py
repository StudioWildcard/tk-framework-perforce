import traceback
from .base_ui import Ui_Generic
from sgtk.platform.qt import QtCore, QtGui
from ..item_schemas import ItemSchema
from ..base_model import MultiModel

class Ui_SyncForm(Ui_Generic):
  
    def __init__(self, parent, app, **kwargs):
        """
        Construction of sync UI
        """    
        self.sync_app = app
        self.sg = self.sync_app.fw



        super().__init__(parent, **kwargs)

        self.sync_app.setup()


    def make_components(self):
        self.schema = ItemSchema

        self.threadpool = QtCore.QThreadPool.globalInstance()
        self.threadpool.setMaxThreadCount(min(23, self.threadpool.maxThreadCount()))


    def make_widgets(self):
        """
        Makes UI widgets for the main form
        """ 



        self.use_filters = ["dog", "cat", "gecko"]

        # bring in global SG search widget when there arent Assets given already to the app
        # search_widget = sgtk.platform.import_framework("tk-framework-qtwidgets", "global_search_widget")
        # self.search_line_edit = search_widget.GlobalSearchWidget(self)    

        self._do = QtGui.QPushButton("Sync")
        self._asset_tree = QtGui.QTreeWidget()

        self._asset_tree.clear()
        self._progress_bar = QtGui.QProgressBar()
        self._list = QtGui.QListWidget()
        self._line_edit = QtGui.QLineEdit()
        self._line_edit.setText(" ")

        self._step_filter_label = QtGui.QLabel("Show/Sync Steps:")
        self._hide_syncd = QtGui.QCheckBox()

        self._force_sync = QtGui.QCheckBox()
        self._force_sync.setText("Force Sync")

        self._rescan = QtGui.QPushButton("Rescan")
         
        # self.data = data

        # self.master_layout = QtGui.QVBoxLayout()
        # self.setLayout(self.master_layout)
        

        # self.proxy_model = SortFilterModel(excludes=['TRex'], parent=self)
        # self.proxy_model.setSourceModel(self.model)
        # self.proxy_model.setDynamicSortFilter(True)


        self.tree_view =QtGui.QTreeView()
        # self.tree_view.setModel(self.model)
        # self.tree_view.setItemDelegateForColumn(1, MultiDelegate(self.tree_view))
        # self.tree_view.setItemDelegateForColumn(2, DoubleSpinBoxDelegate(self.tree_view))
        
        
        # self.list_view = QListView()
        # self.list_view.setModel(self.model)

        # self.table_view = QTableView()
        # self.table_view.setModel(self.model)


        # self.master_layout.addWidget(self.tree_view)
        # self.master_layout.addWidget(self.list_view)
        # self.master_layout.addWidget(self.table_view)

    def reload_view(self):
        try:
            self.logger.debug('attempting to make a model...')
            self.model = MultiModel(self.sync_app.prepared_data)
            self.tree_view.setModel(self.model)
            self.tree_view.expandAll()
            self.logger.info("Reloaded the view")
        except Exception as e:
            import traceback
            self.logger.error(e)
            raise


    def setup_ui(self):
        """
        Lays out and customizes widgets for the main form
        """       
        # set main layout
        self._main_layout = QtGui.QVBoxLayout()
        self._menu_layout = QtGui.QHBoxLayout()
        
        self.setLayout(self._main_layout)

        # hide progress until we run the sync
        self._progress_bar.setVisible(False)

        # set main tree style        
        self._asset_tree.setAnimated(True)
        #self._asset_tree_header = QtGui.QTreeWidgetItem(self.tree_header)
        #self._asset_tree.setHeaderItem(self._asset_tree_header)  
        self._asset_tree.setWordWrap(True)
        self._asset_tree.setColumnWidth(0, 150)
        self._asset_tree.setColumnWidth(1, 160)

        self._hide_syncd.setText("Hide if nothing to sync")



        self._menu_layout.addWidget(self._hide_syncd)
        self._menu_layout.addStretch()

        self.sync_layout = QtGui.QHBoxLayout()
        self.sync_layout.addWidget(self._rescan,  3)
        self.sync_layout.addWidget(self._do,  10)
        self.sync_layout.addWidget(self._force_sync, 1)

        # arrange widgets in layout
        self._main_layout.addLayout(self._menu_layout)
        self._main_layout.addWidget( self.tree_view)
        self._main_layout.addWidget(self._progress_bar)
        self._main_layout.addLayout(self.sync_layout)

        for f in self.use_filters:
            self.button_menu_factory(f)
        
        # connect right_click_menu to tree
        # self._asset_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self._asset_tree.customContextMenuRequested.connect(self.open_context_menu)

        # self._rescan.clicked.connect(self.rescan)
        self.set_ui_interactive(False)


    def button_menu_factory(self, name= None ):
        # sets up a filter for use in 
        width = 80
        short_name = name.lower().replace(" ", "")
        # if name in self.filter_sizes.keys():
        #     width = self.filter_sizes.get(name)

        setattr(self, "_{}_filter".format(short_name), QtGui.QToolButton())
        setattr(self, "_{}_menu".format(short_name), QtGui.QMenu())
        setattr(self, "_{}_actions".format(short_name), {})

        btn = getattr(self, "_{}_filter".format(short_name))
        menu = getattr(self, "_{}_menu".format(short_name))
       
        btn.setFixedWidth(width) 
        btn.setText(name)
        btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        btn.setMenu(menu)
        btn.setPopupMode(QtGui.QToolButton.InstantPopup)

        menu.setFixedWidth(width)
        menu.setTearOffEnabled(True)

        self._menu_layout.addWidget(btn)


    def iterate_progress(self, message=None):
        """
        Iterate global progress counter and update the progressbar widget
        Detect if progress is globally complete and handle hiding the progress widget
        """
        self._progress_bar.setVisible(True)
        self.progress += 1
        
        self._progress_bar.setValue(self.progress)
        # self.set_progress_message(message)
        if self._progress_bar.value() == self._progress_bar.maximum():
            
            self.set_progress_message("{} complete".format(message))
            self._progress_bar.setVisible(False)

            self.set_ui_interactive(True)


    def set_progress_message(self, message=None, percentf=" %p%"):
        """
        Set the message to see in the progress bar
        """
        self._progress_bar.setVisible(True)
        self._progress_bar.setFormat("{}{}".format(message, percentf))


    # def open_context_menu(self, point):
    #     # Infos about the node selected.
    #     try:
    #         os_filebrowser_map = {
    #             "win32" : "Explorer",
    #             "darwin" : "Finder"
    #         }
    #         os_filebrowser = "file browser"
    #         if sys.platform in os_filebrowser_map.keys():
    #             os_filebrowser = os_filebrowser_map[sys.platform]
            
    #         tree_item = self._asset_tree.itemAt(point)
    #         path_to_open = os.path.dirname(tree_item.data(2, QtCore.Qt.UserRole))
        

    #         menu = QtGui.QMenu()
    #         action = menu.addAction("Open path in {}".format(os_filebrowser), 
    #                                 partial(open_browser, path_to_open))
                
    #         menu.exec_(self._asset_tree.mapToGlobal(point))

    #     except Exception as e:
    #         self.log_error(e)
