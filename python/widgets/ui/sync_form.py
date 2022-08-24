from logging import Filter
import traceback
import os

from .base_ui import Ui_Generic
from sgtk.platform.qt import QtCore, QtGui
from ..item_schemas import RowSchema
from ..base_model import MultiModel
from ..filter_models import SortFilterModel

from ..utils import open_browser, trace, method_decorator


@method_decorator(trace)
class Ui_SyncForm(Ui_Generic):
    def __init__(self, parent, app, **kwargs):
        """
        Construction of sync UI
        """
        self.progress_handler = None

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
        self.proxy_model = SortFilterModel(excludes=[None], parent=self)
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
        self._global_progress_bar = QtGui.QProgressBar()
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
        # self.tree_view.setColumnWidth(1, 200)

        # self.tree_view.setIconSize(10)

        self.view_stack.addWidget(self.tree_view)
        self.view_stack.addWidget(self.b)
        self.view_stack.setCurrentWidget(self.b)

        # set main tree style
        self._asset_tree.setAnimated(True)
        # self._asset_tree_header = QtGui.QTreeWidgetItem(self.tree_header)
        # self._asset_tree.setHeaderItem(self._asset_tree_header)
        self._asset_tree.setWordWrap(True)

        self._hide_syncd.setText("Hide if nothing to sync")

        self._global_progress_bar.setMaximumHeight(10)

        self._menu_layout.addWidget(self._hide_syncd)
        self._menu_layout.addStretch()

        self.sync_layout = QtGui.QHBoxLayout()
        self.sync_layout.addWidget(self._rescan, 3)
        self.sync_layout.addWidget(self._do, 10)
        self.sync_layout.addWidget(self._force_sync, 1)

        # arrange widgets in layout
        self._main_layout.addLayout(self._menu_layout)
        self._main_layout.addWidget(self.view_stack)
        self._main_layout.addWidget(self._global_progress_bar)
        self._main_layout.addWidget(self._progress_bar)
        self._main_layout.addLayout(self.sync_layout)

        self._rescan.clicked.connect(self.filtered)

        for widget in [self._do, self._force_sync, self._rescan]:  # , self.tree_view]:
            self.centrally_control_enabled_state(widget)

        for f in self.use_filters:
            self.button_menu_factory(f)

        # connect right_click_menu to tree
        # self._asset_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self._asset_tree.customContextMenuRequested.connect(self.open_context_menu)

        # self._rescan.clicked.connect(self.rescan)

        self.resize(1000, 1000)

        self.setup_views()

        # self.interactive = False
        self.show_waiting()

    def setup_events(self):
        self._do.clicked.connect(self.start_sync)

    def update_progress(self):
        if len(self.progress_handler.queue.keys()) > 1:
            self._global_progress_bar.setVisible(True)
        self._global_progress_bar.setRange(0, 100)
        self._progress_bar.setVisible(True)
        self._progress_bar.setRange(0, 100)
        if not self.progress_handler.progress == 1:
            self._progress_bar.setValue(self.progress_handler.progress * 100)
            self._global_progress_bar.setValue(
                self.progress_handler.meta_tracker.progress * 100
            )
        else:
            self._progress_bar.setVisible(False)
            self._progress_bar.setValue(0)
            self._global_progress_bar.setVisible(False)
            self._global_progress_bar.setValue(0)

    def icon_path(self, name) -> str:
        icon_path = self.sync_app.shotgun_globals.icon.get_entity_type_icon_url(name)
        if not icon_path:
            icon_path = os.path.join(
                self.sync_app.basepath, "resources", "status_{}.png".format(name)
            )
        return icon_path

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

                self.logger.debug(
                    "Filter added: {}:{}".format(filter_type, filter_value)
                )

        except Exception as e:

            self.logger.error(traceback.format_exc())

    def setup_views(self):
        if getattr(self.model.rootItem, "column_schema"):
            schema = self.model.rootItem.column_schema
            for view in [self.tree_view]:
                self.logger.info("setting up view: {}".format(schema))
                for c, col_def in enumerate(schema):
                    if col_def.get("width"):
                        view.setColumnWidth(c, col_def["width"])

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
        self.filtered()

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

    def filtered(self):
        self.model.refresh()
        # self.tree_view.resizeColumnToContents(0)

    def show_tree(self):
        self.view_stack.setCurrentWidget(self.tree_view)

    def show_waiting(self):
        self.view_stack.setCurrentWidget(self.b)
