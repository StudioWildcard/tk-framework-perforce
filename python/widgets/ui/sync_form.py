import traceback
from .base_ui import Ui_Generic
from sgtk.platform.qt import QtCore, QtGui
from ..item_schemas import ItemSchema
from ..base_model import MultiModel
from ..filter_models import SortFilterModel

class Ui_SyncForm(Ui_Generic):
  
    def __init__(self, parent, app, **kwargs):
        """
        Construction of sync UI
        """    
        self.sync_app = app
        self.sg = self.sync_app.fw
        self.sync_app.ui = self 


        super().__init__(parent, **kwargs)
        
        self.sync_app.setup()


    def make_components(self):

        # the utility that defines how we hand raw data to the model
        self.schema = ItemSchema

        # the utility that routes the data into a table/view
        self.model = MultiModel()
        
        # the filtering/sorting utility that uses our existing model to modify
        self.proxy_model = SortFilterModel(excludes=['aaaaaaaaaaaa'], parent=self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        self.proxy_model = self.model

        # the threadpool we send thread workers to.
        self.threadpool = QtCore.QThreadPool.globalInstance()
        self.threadpool.setMaxThreadCount(min(23, self.threadpool.maxThreadCount()))


    def make_widgets(self):
        """
        Makes UI widgets for the main form
        """ 
        self.use_filters = ["dog", "cat", "gecko"]
 

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
        



        self.tree_view =QtGui.QTreeView()
        
        self.view_stack = QtGui.QStackedWidget()
        self.b = QtGui.QLabel("Gathering contextual request from Perforce Servers for {} items...".format(str(len(self.sync_app.input_data))))


    def reload_view(self):
        
        try:
            self.tree_view.update()
            self.tree_view.expandAll()
            self.tree_view.setAnimated(True)
        except Exception as e:
            import traceback
            self.logger.error(e)
            raise


    def setup_style(self):
        self.setStyleSheet("""
            QTreeView::item { padding: 5px; }
            QAction  { padding: 10px; }
        """ )


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

        self.tree_view.setModel(self.proxy_model)
        self.tree_view.setAnimated(True)

        self.view_stack.addWidget(self.tree_view)
        self.view_stack.addWidget(self.b)
        self.view_stack.setCurrentWidget(self.b)

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
        self._main_layout.addWidget( self.view_stack)
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


    def set_ready(self, state):
        if state:
            self.view_stack.setCurrentWidget(self.tree_view)
        else:
            self.view_stack.setCurrentWidget(self.b)


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
