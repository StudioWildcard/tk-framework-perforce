import traceback
from .base_ui import Ui_Generic


class Ui_SyncForm(Ui_Generic):
  
    def __init__(self, parent, **kwargs):
        """
        Construction of sync UI
        """
        super().__init__(parent, **kwargs)



    def make_widgets(self):
        """
        Makes UI widgets for the main form
        """

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
        self._main_layout.addWidget( self._asset_tree)
        self._main_layout.addWidget(self._progress_bar)
        self._main_layout.addLayout(self.sync_layout)

        # for f in self.use_filters:
        #     self.button_menu_factory(f)
        
        # connect right_click_menu to tree
        # self._asset_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self._asset_tree.customContextMenuRequested.connect(self.open_context_menu)

        # self._rescan.clicked.connect(self.rescan)
        self.set_ui_interactive(False)



