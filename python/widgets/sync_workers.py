from webbrowser import get
import sgtk
from sgtk.platform.qt import QtCore, QtGui
import os
import traceback
import pprint
import random
import time
import uuid
import copy

from ..sync.resolver import TemplateResolver
from ..util.view import get_client_view, set_client_view, add_paths_to_view
from .utils import method_decorator, trace


class SyncSignaller(QtCore.QObject):
    """
    Create signaller class for Sync Worker, required for using signals due to QObject inheritance
    """

    started = QtCore.Signal(dict)
    finished = QtCore.Signal()
    completed = QtCore.Signal(dict)  # (path to sync, p4 sync response)


class AssetInfoGatherSignaller(QtCore.QObject):
    """
    Create signaller class for AssetInfoGather Worker, required for using signals due to QObject inheritance
    """

    progress = QtCore.Signal(str)
    root_path_resolved = QtCore.Signal(str)
    info_gathered = QtCore.Signal(dict)
    item_found_to_sync = QtCore.Signal(dict)
    status_update = QtCore.Signal(str)
    includes = QtCore.Signal(tuple)
    gathering_complete = QtCore.Signal(dict)
    total_items_found = QtCore.Signal(dict)


# class SyncWorker2(QtCore.QRunnable):

#     # structurally anticipate basic p4 calls, which will route to the main form.
#     p4 = None
#     fw = None
#     path_to_sync = None
#     asset_name = None

#     def __init__(self):
#         """
#         Handles syncing specific file from perforce depot to local workspace on disk
#         """
#         super(SyncWorker, self).__init__()
#         self.signaller = SyncSignaller()

#         # use signals from Signaller, since we cant in a non-QObject derrived
#         # object like this QRunner.
#         self.started = self.signaller.started
#         self.finished = self.signaller.finished
#         self.progress = self.signaller.progress

#     def log_error(self, e):
#         self.fw.log_error(str(e))
#         self.fw.log_error(traceback.format_exc())

#     @QtCore.Slot()
#     def run(self):

#         """
#         Ryn syncs from perforce, signals information back to main thread.
#         """
#         self.p4 = self.fw.connection.connect()

#         # self.fw.log_debug("starting thread in pool to sync {}".format(self.path_to_sync))
#         self.started.emit(
#             {"asset_name": self.asset_name, "sync_path": self.path_to_sync}
#         )

#         # run the syncs
#         p4_response = self.p4.run("sync", ["-f"], "{}#head".format(self.path_to_sync))
#         self.fw.log_debug(p4_response)

#         # emit item key and p4 response to main thread
#         self.progress.emit(
#             {
#                 "asset_name": self.asset_name,
#                 "sync_path": self.path_to_sync,
#                 "response": p4_response,
#             }
#         )


@method_decorator(trace)
class SyncWorker(QtCore.QRunnable):

    # structurally anticipate basic p4 calls, which will route to the main form.
    p4 = None

    path_to_sync = None
    asset_name = None
    item = None

    def __init__(self):
        """
        Handles syncing specific file from perforce depot to local workspace on disk
        """
        super(SyncWorker, self).__init__()
        self.signaller = SyncSignaller()

        # use signals from Signaller, since we cant in a non-QObject derrived
        # object like this QRunner.
        self.started = self.signaller.started
        self.finished = self.signaller.finished
        self.completed = self.signaller.completed

    def log_error(self, e):
        self.fw.log_error(str(e))
        self.fw.log_error(traceback.format_exc())

    @QtCore.Slot()
    def run(self):

        """
        Ryn syncs from perforce, signals information back to main thread.
        """
        try:
            self.started.emit({"model_item": self.id})
            self.p4 = self.fw.connection.connect()
            # # run the syncs
            p4_response = self.p4.run(
                "sync", ["-f"], "{}#head".format(self.path_to_sync)
            )
            self.fw.log_debug(p4_response)

            # emit item key and p4 response to main thread
            self.completed.emit({"model_item": self.id, "path": self.path_to_sync})
        except Exception as e:
            import traceback

            self.completed.emit(
                {
                    "model_item": self.id,
                    "path": self.path_to_sync,
                    "error": traceback.format_exc(),
                }
            )


@method_decorator(trace)
class AssetInfoGatherWorker(QtCore.QRunnable):
    def __init__(self, app=None, entity=None, framework=None):
        """
        Handles gathering information about specific asset from SG and gets related Perforce information
        """
        super(AssetInfoGatherWorker, self).__init__()

        self.id = str(uuid.uuid4())

        self.app = app
        self.entities = entity

        self.force_sync = False

        self._items_to_sync = []
        self._status = None
        self._icon = None
        self._detail = None

        self.fw = framework
        self.asset_item = None

        self.progress_batch_size = 0
        self.progress_batch_completion = 0

        self.signaller = AssetInfoGatherSignaller()

        self.info_gathered = self.signaller.info_gathered
        self.progress = self.signaller.progress
        self.root_path_resolved = self.signaller.root_path_resolved
        self.item_found_to_sync = self.signaller.item_found_to_sync
        self.status_update = self.signaller.status_update
        self.includes = self.signaller.includes
        self.total_items_found = self.signaller.total_items_found
        self.gathering_complete = self.signaller.gathering_complete

        self.publish_file = False

    def log_error(self, e):
        self.fw.log_error(str(e))
        self.fw.log_error(traceback.format_exc())

    @property
    def asset_name(self):
        try:
            name = None
            if self.asset_item.get("context"):
                name = self.asset_item.get("context").entity.get("name")
            if not name:
                if self.entity.get("code"):
                    name = self.entity.get("code")
                else:
                    name = self.app.shotgun.find_one(
                        self.entity.get("type"),
                        [["id", "is", self.entity.get("id")]],
                        ["code"],
                    ).get("code")

            if self.entity.get("type") in ["PublishFiles"]:
                sg_ret = self.app.shotgun.find_one(
                    "Asset",
                    [["id", "is", self.entity.get("entity").get("id")]],
                    ["code"],
                )
                name = sg_ret.get("code")
            return name
        except Exception as e:
            import traceback

            self.log_error(traceback.format_exc())

    @property
    def root_path(self):
        rp = self.asset_item.get("root_path")
        if self.entity.get("type") in ["PublishedFile"]:
            # TODO: this needs to become dynamic
            rp = "B:/" + self.entity.get("path_cache")
        return rp

    @property
    def status(self):
        if self.asset_item.get("error"):
            self._icon = "warning"
            self._status = "Error"
            self._detail = self.asset_item.get("error")
        return self._status

    def collect_and_map_info(self):
        """
        Call perforce for response and form data we will signal back
        """
        if self.status != "error":
            self.get_perforce_sync_dry_reponse()

        # payload that we'll send back to the main thread to make UI item with
        self.info_to_signal = {
            "asset_name": self.asset_name,
            "root_path": self.root_path,
            "status": self._status,
            "details": self._detail,
            "icon": self._icon,
            "asset_item": self.asset_item,
            "items_to_sync": self._items_to_sync,
        }

    def get_perforce_sync_dry_reponse(self):
        """
        Get a response from perforce about our wish to sync a specific asset root path,
        Contextually use response to drive our status that we show the user. 1
        """
        if self.root_path and (self.entity.get("type") not in ["PublishedFile"]):

            # self.fw.log_error(self.p4.run("client"))
            arguments = ["-n", "--parallel=threads=6"]
            if self.force_sync:
                arguments.append("-f")
            sync_response = self.p4.run("sync", arguments)

            if not sync_response:
                self._status = "Not In Depot"
                self._icon = "error"
                self._detail = "Nothing in depot resolves [{}]".format(self.root_path)

            elif len(sync_response) is 1 and type(sync_response[0]) is str:
                self._status = "Syncd"
                self._icon = "success"
                self._detail = "Nothing new to sync for [{}]".format(self.root_path)
            else:
                # if the response from p4 has items... make UI elements for them
                self._items_to_sync = [i for i in sync_response if type(i) != str]
                self._status = "{} items to Sync".format(len(self._items_to_sync))
                self._icon = "load"
                self._detail = self.root_path
        if self.entity.get("type") in ["PublishedFile"]:
            self._items_to_sync = [
                {"clientFile": "B:/" + self.entity.get("path_cache")}
            ]
            self._status = "Exact Path"
            self._detail = "Exact path specified: [{}]".format(self.root_path)
            self._icon = "load"
            self.fw.log_info(self._items_to_sync)

    @QtCore.Slot()
    def run_old(self):
        self.item_found_to_sync.emit({"message": "works"})

    @QtCore.Slot()
    def run(self):

        """
        Checks if there are errors in the item, signals that, or if not, gets info regarding what there is to sync.
        """
        # time.sleep(random.randint(0, 12))

        # self.p4 = self.fw.connection.connect()
        # set_client_view(self.p4, [])

        self.p4 = self.fw.connection.connect()
        view = []
        paths = []

        self.asset_map = {}

        # make a maps of everything based on the sync_root

        for i in self.entities:
            # time.sleep(2)
            self.entity = i
            # try:
            self.template_resolver = TemplateResolver(app=self.app, entity=self.entity)

            self.asset_item = self.template_resolver.entity_info
            key = self.asset_item.get("root_path")[:-5].replace("/", "\\")
            self.asset_map[key] = {
                "asset": copy.deepcopy(self.asset_item),
                "entity": copy.deepcopy(self.entity),
            }
            paths.append(self.asset_item.get("root_path"))

        self.p4 = add_paths_to_view(self.p4, paths)

        # self.p4.run("client")
        progress_status_string = ""

        self.status_update.emit(
            "Requesting sync information for {}".format(self.asset_name)
        )

        # self.fw.log_info(self.asset_item)
        self.collect_and_map_info()

        # self.info_gathered.emit(self.info_to_signal)
        if self.status == "Syncd":
            progress_status_string = " (Nothing to sync. Skipping...)"

        if self.status != "Error":

            self.total_items_found.emit(
                {"id": self.id, "count": len(self._items_to_sync)}
            )

            if self._items_to_sync:
                # make lookup list for SG api call for published files to correlate.
                depot_files = [i.get("depotFile") for i in self._items_to_sync]
                find_fields = [
                    "sg_p4_change_number" "code",
                    "entity.Asset.code" "sg_p4_depo_path",
                    "task.Task.step.Step.code",
                    "published_file_type.PublishedFileType.code",
                ]

                sg_filter = ["sg_p4_depo_path", "in", depot_files]
                if self.entity.get("type") in ["PublishedFile"]:
                    sg_filter = ["id", "in", self.entity.get("id")]
                published_files = self.app.shotgun.find(
                    "PublishedFile", [sg_filter], find_fields
                )
                published_file_by_depot_file = {
                    i.get("sg_p4_depo_path"): i for i in published_files
                }
                # self.fw.log_info(published_file_by_depot_file)
                for item in self._items_to_sync:

                    # published_file = published_file_by_depot_file.get(
                    #     item.get("depotFile")
                    # )

                    for i in self.asset_map.keys():
                        # self.log_error(i)
                        # self.log_error(item.get("clientFile"))
                        if i in item.get("clientFile"):
                            self.asset_item = self.asset_map[i]["asset"]
                            self.entity = self.asset_map[i]["entity"]

                    step = None

                    file_type = None
                    # if published_file:
                    #     # self.fw.log_info(published_file_by_depot_file)

                    #     step = published_file.get("task.Task.step.Step.code")
                    #     file_type = published_file.get(
                    #         "published_file_type.PublishedFileType.code"
                    #     )

                    #     if file_type:
                    #         self.includes.emit(("type", file_type))

                    # if step:
                    #     self.includes.emit(("step", step))

                    ext = None
                    if "." in item.get("clientFile"):
                        ext = os.path.basename(item.get("clientFile")).split(".")[-1]
                        self.includes.emit(("ext", ext.lower()))

                    status = item.get("action")
                    if self.entity.get("type") in ["PublishedFile"]:
                        status = "Exact File"
                    # time.sleep(0.017)
                    self.item_found_to_sync.emit(
                        {
                            "worker_id": self.id,
                            "asset_name": self.asset_name,
                            "item_found": item,
                            "step": step,
                            "type": file_type,
                            "ext": ext.lower(),
                            "status": status,
                        }
                    )
        else:
            progress_status_string = " (Encountered error. See details)"
        self.fw.log_info(progress_status_string)

        # except Exception as e:
        #     import traceback

        #     self.log_error(traceback.format_exc())

        # self.info_gathered.emit({"status": "gathered"})
