import traceback
import os

from .base_ui import Ui_Generic
from sgtk.platform.qt import QtCore, QtGui
from ..item_schemas import RowSchema
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
        self.schema = RowSchema

        # the utility that routes the data into a table/view
        self.model = MultiModel(parent=self)

        # the filtering/sorting utility that uses our existing model to modify
        self.proxy_model = SortFilterModel(excludes=["aaaaaaaaaaaa"], parent=self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        # self.proxy_model = self.model

        # the threadpool we send thread workers to.
        self.threadpool = QtCore.QThreadPool.globalInstance()
        self.threadpool.setMaxThreadCount(min(23, self.threadpool.maxThreadCount()))

    def make_widgets(self):
        """
        Makes UI widgets for the main form
        """
        self.use_filters = ["ext"]

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

        self.tree_view = QtGui.QTreeView()

        self.view_stack = QtGui.QStackedWidget()
        self.b = QtGui.QLabel(
            "<center><h3>Gathering contextual request from Perforce Servers for:<br></h3><h5> {} items...</center>".format(
                str(len(self.sync_app.input_data))
            )
        )

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
        self.setStyleSheet(
            """
            QTreeView::item { padding: 5px; }
            QAction  { padding: 10px; }
        """
        )

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
        self.tree_view.setColumnWidth(1, 200)

        self.view_stack.addWidget(self.tree_view)
        self.view_stack.addWidget(self.b)
        self.view_stack.setCurrentWidget(self.b)

        # set main tree style
        self._asset_tree.setAnimated(True)
        # self._asset_tree_header = QtGui.QTreeWidgetItem(self.tree_header)
        # self._asset_tree.setHeaderItem(self._asset_tree_header)
        self._asset_tree.setWordWrap(True)
        self._asset_tree.setColumnWidth(0, 150)
        self._asset_tree.setColumnWidth(1, 190)

        self._hide_syncd.setText("Hide if nothing to sync")

        self._menu_layout.addWidget(self._hide_syncd)
        self._menu_layout.addStretch()

        self.sync_layout = QtGui.QHBoxLayout()
        self.sync_layout.addWidget(self._rescan, 3)
        self.sync_layout.addWidget(self._do, 10)
        self.sync_layout.addWidget(self._force_sync, 1)

        # arrange widgets in layout
        self._main_layout.addLayout(self._menu_layout)
        self._main_layout.addWidget(self.view_stack)
        self._main_layout.addWidget(self._progress_bar)
        self._main_layout.addLayout(self.sync_layout)

        self._rescan.clicked.connect(self.filterd)

        for widget in [self._do, self._force_sync, self._rescan, self.tree_view]:
            self.centrally_control_enabled_state(widget)

        for f in self.use_filters:
            self.button_menu_factory(f)

        # connect right_click_menu to tree
        # self._asset_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self._asset_tree.customContextMenuRequested.connect(self.open_context_menu)

        # self._rescan.clicked.connect(self.rescan)
        self.interactive = False
        self.show_waiting()

    def icon_path(self, name) -> str:
        return os.path.join(
            self.sync_app.basepath, "resources", "status_{}.png".format(name)
        )

    def make_icon(self, name) -> QtGui.QIcon:
        """
        Convenience maker of icons if following a given naming pattern.

        Args:
            name (str): name of the icon on disk, to be inserted into `status_{}.png`

        Returns:
            QtGui.QIcon: Path'd QIcon ready to set to a button or widget's setIcon() func
        """
        import os

        return QtGui.QIcon(self.icon_path(name))

    def update_available_filters(self, filter_info):
        """

        TODO: implement during scraping/transformation of data
        Populate the steps filter menu as steps are discovered in the p4 scan search
        """
        try:
            filter_type = filter_info[0]
            filter_value = filter_info[1]

            actions = getattr(self, "_{}_actions".format(filter_type))
            # if actions:
            if filter_value not in actions.keys():
                action = QtGui.QAction(self)

                action.setCheckable(True)

                self.utils.prefs.read()
                filters = self.utils.prefs.data.get("{}_filters".format(filter_type))
                check_state = True
                if filters:
                    if filter_value in filters.keys():
                        check_state = filters[filter_value]

                action.setChecked(check_state)
                action.setText(str(filter_value))
                action.triggered.connect(self.filter_triggered)
                #  action.triggered.connect(self.filter_items)

                getattr(self, "_{}_menu".format(filter_type)).addAction(action)
                actions[filter_value] = action

        except Exception as e:
            self.logger.error(e)

    def filter_triggered(self):
        data = self.utils.prefs.read()
        for f in self.use_filters:
            f = f.lower()
            filter_name = "{}_filters".format(f)
            filter_data = {}

            # use existing filter data if exists
            if data.get(filter_name):
                filter_data = data.get(filter_name)
            # overwrite it with  our scan of presently checked items
            if hasattr(self, "_{}_actions".format(f)):
                actions = getattr(self, "_{}_actions".format(f))
                if actions:
                    for k, v in actions.items():
                        filter_data[k] = v.isChecked()

            data[filter_name] = filter_data

            self.utils.prefs.write(data)

    def button_menu_factory(self, name=None):
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

        self.logger.error(str(getattr(self, "_{}_actions".format(short_name))))

        self._menu_layout.addWidget(btn)

    def filterd(self):
        self.model.refresh()

    def show_tree(self):
        self.view_stack.setCurrentWidget(self.tree_view)

    def show_waiting(self):
        self.view_stack.setCurrentWidget(self.b)

    # def iterate_progress(self, message=None):
    #     """
    #     Iterate global progress counter and update the progressbar widget
    #     Detect if progress is globally complete and handle hiding the progress widget
    #     """
    #     self._progress_bar.setVisible(True)
    #     self.progress += 1

    #     self._progress_bar.setValue(self.progress)
    #     # self.set_progress_message(message)
    #     if self._progress_bar.value() == self._progress_bar.maximum():

    #         self.set_progress_message("{} complete".format(message))
    #         self._progress_bar.setVisible(False)

    #         self.set_ui_interactive(True)

    # def set_progress_message(self, message=None, percentf=" %p%"):
    #     """
    #     Set the message to see in the progress bar
    #     """
    #     self._progress_bar.setVisible(True)
    #     self._progress_bar.setFormat("{}{}".format(message, percentf))

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

    # def sync_in_progress(self, sync_item):
    #     """
    #     TODO:
    #     Handle signal from SyncWorker.started to inform user that sync has started within sync_item_widget.
    #     This sync_item_widget is looked up from our global asset dictionary using the signal payload arg [dict]
    #     """

    #     asset_name = sync_item.get("asset_name")
    #     sync_path = sync_item.get("sync_path")

    #     sync_item_widget = (
    #         self._asset_items[asset_name].get("child_widgets").get(sync_path)
    #     )
    #     asset_item_widget = self._asset_items[asset_name].get("tree_widget")

    #     icon = self.make_icon("syncing")
    #     sync_item_widget.setIcon(1, icon)
    #     sync_item_widget.setText(1, "Syncing")

    #     self._asset_tree.scrollTo(self._asset_tree.indexFromItem(sync_item_widget))
    #     asset_item_widget.setExpanded(True)

    # def item_syncd(self, sync_item):
    #     """
    #     TODO: add functionality to model or item method
    #     Handle signal from SyncWorker.progress to display sync status in sync_item_widget.
    #     This sync_item_widget is looked up from our global asset dictionary using the signal payload arg [dict]
    #     """

    #     # log status of sync for this item
    #     asset_name = sync_item.get("asset_name")
    #     sync_path = sync_item.get("sync_path")
    #     response = sync_item.get("response")

    #     # self.fw.log_debug(sync_path)

    #     # look up the sync-item object since we're passing only a topic/string around via signal
    #     child_widgets = self._asset_items[asset_name].get("child_widgets")
    #     sync_item_widget = child_widgets.get(sync_path)
    #     asset_item_widget = self._asset_items[asset_name].get("tree_widget")

    #     # since we're getting this
    #     icon = self.make_icon("success")
    #     sync_item_widget.setIcon(1, icon)
    #     sync_item_widget.setText(1, "Syncd")

    #     # check how many asset children are still needing to be synced
    #     count_left_to_sync = len(
    #         [
    #             sync_widget
    #             for sync_path, sync_widget in child_widgets.items()
    #             if sync_widget.text(1) == "Ready"
    #         ]
    #     )

    #     # set parent
    #     parent_asset_status = "{} item{} to sync"
    #     plurality = ""
    #     if count_left_to_sync > 0:
    #         if count_left_to_sync > 1:
    #             plurality = "s"

    #         # set asset parent's status regarding count-left-to-sync
    #         asset_item_widget.setText(
    #             1, parent_asset_status.format(count_left_to_sync, plurality)
    #         )
    #     else:
    #         # when all sync's are done...
    #         icon = self.make_icon("validate")
    #         asset_item_widget.setIcon(1, icon)
    #         asset_item_widget.setText(1, "Asset in Sync")

    #     self.iterate_progress(message="Syncing {}".format(sync_item_widget.text(0)))

    # def start_sync(self):
    #     """
    #     Iterate through assets and their sync items to start workers for all paths that require syncs.
    #     Utilize a global threadpool to process
    #     """
    #     try:
    #         self.interactive = False

    #         workers = []
    #         for asset_name, asset_dict in self._asset_items.items():
    #             for sync_path, sync_widget in asset_dict["child_widgets"].items():
    #                 if not sync_widget.isHidden():
    #                     sync_worker = SyncWorker()
    #                     sync_worker.path_to_sync = sync_path
    #                     sync_worker.asset_name = asset_name

    #                     sync_worker.fw = self.fw

    #                     sync_worker.started.connect(self.sync_in_progress)
    #                     # worker.finished.connect(self.sync_completed)
    #                     sync_worker.progress.connect(self.item_syncd)

    #                     workers.append(sync_worker)

    #         self.progress = 0

    #         self.progress_maximum = len(workers)
    #         self._progress_bar.setRange(0, self.progress_maximum)
    #         self._progress_bar.setValue(0)
    #         self._progress_bar.setVisible(True)
    #         self._progress_bar.setFormat("%p%")

    #         # make threadpool to take all workers and multithread their execution
    #         # self.threadpool = QtCore.QThreadPool.globalInstance()
    #         # self.threadpool.setMaxThreadCount(min(24, self.threadpool.maxThreadCount()))

    #         # self.fw.log_debug("Starting Threaded P4 Sync...")

    #         # setup workers for multiprocessing

    #         for sync_worker in workers:
    #             sync_worker.run()
    #     except Exception as e:
    #         self.log_error(e)
