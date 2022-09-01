from inspect import trace
import os
import traceback
import pprint
import random
import time
import sys
import pprint


import sgtk
from sgtk import TankError
from sgtk.platform.qt import QtCore, QtGui
from functools import partial

from .sync_workers import SyncWorker, AssetInfoGatherWorker
from .utils import PrefFile, open_browser, partialclass, trace, method_decorator
from .ui.sync_form import Ui_SyncForm
from .progress import ProgressHandler


@method_decorator(trace)
class SyncApp:

    _fw = None
    _p4 = None
    _ui = None

    progress = 0

    def __init__(
        self, parent_sgtk_app, entities_to_sync, specific_files, parent=None, data=None
    ):

        """
        Construction of sync app
        """
        self.parent = parent

        self.progress_handler = ProgressHandler()

        self.workers = {"asset_info": AssetInfoGatherWorker, "sync": SyncWorker}
        self.shotgun_globals = sgtk.platform.import_framework(
            "tk-framework-shotgunutils", "shotgun_globals"
        )

        # the threadpool we send thread workers to.
        self.threadpool = QtCore.QThreadPool.globalInstance()
        self.threadpool.setMaxThreadCount(min(23, self.threadpool.maxThreadCount()))

        # file base for accessing Qt resources outside of resource scope
        self.basepath = os.path.dirname(os.path.abspath(__file__))

        self.entities_to_sync = entities_to_sync
        self.input_data = self.entities_to_sync
        self.prepared_data = []

        self.parent_sgtk_app = parent_sgtk_app

    @property
    def logger(self):
        return self.parent_sgtk_app.logger

    @property
    def ui(self):
        # if not self._ui:
        #     self._ui = self.ui_class()
        return self._ui

    @ui.setter
    def ui(self, ui):
        self._ui = ui

    @property
    def ui_class(self):
        return partialclass(
            Ui_SyncForm, self.parent, self, logger=self.parent_sgtk_app.logger
        )

    def run(self):
        """
        Assumes we arent handling the UI elsewhere, and want to launch it here.
        """
        import sys

        app = QtGui.QApplication(sys.argv)
        ui = Ui_SyncForm(self.parent, self)
        # sys.exit()
        ui.show()
        ui.render_to_image()
        app.exec_()

    @property
    def fw(self):
        """
        Implement framework if doesnt currently exist,  return it if it does
        """
        if not self._fw:
            self._fw = sgtk.platform.current_bundle()
        return self._fw

    @property
    def p4(self):
        """
        initializes p4 as connection setup if it doesnt exist. Passes existing if it does.
        """
        if not self._p4:
            self._p4 = self.fw.connection.connect()
        return self._p4

    def setup(self):
        """
        We defer the init so that the app can begin setting itself up when
        the UI is ready/built. This method is called by the app.

        TODO: to speed up our data collection, we should be collecting
        from the moment the app is created, and then have a our setup
        gather the information

        """
        self.initialize_data()

        self.ui._do.clicked.connect(self.start_sync)

        self.logger.info(f"App build completed with workers")

    def track_new_progress(self, progress):
        """
        Register a new progress tracker so multiple
        sources can contribute to global progress

        Args:
            progress (dict): dict from workers reporting item count to iterate

        """
        self.progress_handler.track_progress(
            items=progress.get("count"), id=progress.get("id")
        )

    def report_worker_info(self, item: dict) -> None:
        """
        Method to process incoming dictionaries regarding items found
        to sync.  This is connected to the worker thread's singal
        emitter so it is triggered automatically.

        Args:
            item (dict): dictionary with P4/SG single file sync information
                        ...
                        asset_name: str
                        item_found
        Raises:
            sgtk.TankError: _description_
        """
        # let's announce what the item was
        # self.logger.info(
        #     "Item received from worker thread:\n{}".format(pprint.pformat(item))
        # )
        self.logger.info(item)

        if not self.ui.progress_handler:
            self.ui.progress_handler = self.progress_handler
        self.progress_handler.tracker(item.get("worker_id")).iterate()
        self.ui.update_progress()

        # we'll add a row to our model.
        # the "row" we're adding is a dictionary, but since the model has
        # its own parenting logic, it may ultimately be 2 items created in the model:
        # a parent for the sync item, and the sync item. If the parent already exists,
        # it will create just the sync item.
        self.ui.model.add_row(item)
        self.ui.reload_view()

        # we want to let the UI know we're ready to see the data that's
        # just been updated
        self.ui.show_tree()

    def data_gathering_complete(self, completion_dict: dict) -> None:
        """
        General app method to be utilized by worker threads so that they can
        report completion.

        Args:
            completion_dict (dict)
        """

        self.logger.info("Finished gathering data from perforce.")
        self.ui.interactive = True

    def initialize_data(self):
        """
        Iterate through tk-multi-perforce delivered list of asset information,
        Utilize a global threadpool to process workers to ask P4 server for what
        there is to sync for these.
        """
        asset_info_gather_worker = AssetInfoGatherWorker(
            app=self.parent_sgtk_app, entity=self.input_data, framework=self.fw
        )

        asset_info_gather_worker.p4 = self.p4

        # as workers emit the item_found_to_sync, hit that method with the payload from it
        asset_info_gather_worker.item_found_to_sync.connect(self.report_worker_info)
        asset_info_gather_worker.info_gathered.connect(self.data_gathering_complete)
        asset_info_gather_worker.total_items_found.connect(self.track_new_progress)
        asset_info_gather_worker.includes.connect(self.ui.update_available_filters)

        # this adds to the threadpool and runs the `run` method on the QRunner.
        self.threadpool.start(asset_info_gather_worker)

    def item_starting_sync(self, status_dict):
        # make sure that the item knows its syncing,
        item = self.item_map.get(status_dict.get("model_item"))
        item.syncing = True
        self.ui.reload_view()

    def item_completed_sync(self, status_dict):
        item = self.item_map.get(status_dict.get("model_item"))
        self.progress_handler.tracker("sync_workers").iterate()
        self.ui.update_progress()

        self.logger.info(status_dict.get("path"))

        item.syncing = False

        if status_dict.get("error"):
            item.error = status_dict["error"]
        else:
            item.syncd = True
        self.ui.reload_view()

    def start_sync(self):
        """
        Iterate through assets and their sync items to start workers for all paths that require syncs.
        Utilize a global threadpool to process
        """

        self.ui.interactive = False

        # hold a map to our items while they process
        self.item_map = {}

        workers = []
        for asset in self.ui.model.rootItem.childItems:
            for sync_item in asset.childItems:
                if sync_item.visible:
                    # self.logger.info(str(sync_item))
                    sync_worker = SyncWorker()

                    self.item_map[sync_item.id] = sync_item
                    sync_worker.id = sync_item.id

                    sync_worker.path_to_sync = sync_item.data(5)
                    sync_worker.asset_name = sync_item.parent().data(1).split(" ")[0]

                    sync_worker.fw = self.fw

                    sync_worker.started.connect(self.item_starting_sync)
                    sync_worker.completed.connect(self.item_completed_sync)

                    workers.append(sync_worker)

        queue_length = len(workers)

        self.track_new_progress({"count": queue_length, "id": "sync_workers"})

        for worker in workers:
            self.threadpool.start(worker)
