# Copyright (c) 2013 Studio WILDCARD.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.


from inspect import trace
import os
import traceback
import pprint
import random
import time
import sys

import sgtk
from sgtk import TankError
from sgtk.platform.qt import QtCore, QtGui
from functools import partial

from .sync_workers import SyncWorker, AssetInfoGatherWorker
from .utils import PrefFile, open_browser, partialclass
from .ui.sync_form import Ui_SyncForm

# file base for accessing Qt resources outside of resource scope
basepath = os.path.dirname(os.path.abspath(__file__))

class SyncApp():

    _fw = None
    _p4 = None
    _ui = None
        
    progress = 0
    
    def __init__(self, parent_sgtk_app, entities_to_sync, specific_files,  parent=None, data=None):
        
        """
        Construction of sync UI
        """
        self.parent = parent
        
        self.workers = {
            "asset_info": AssetInfoGatherWorker,
            "sync" : SyncWorker
        }
        # self.data = [
        #     {'asset': "Ankylo",
        #     "sync_filename" : "Ankylo_concept_v001.psd",
        #     "sync_path": "/shows/test/Ankylo_concept_v001.psd",
        #     "status" : "Peaceful",
        #     "version": 1
        #     },
        #     {'asset': "Ankylo2",
        #     "sync_filename" : "Ankylo2_concept_v001.psd",
        #     "sync_path": None,
        #     "status" : "Peaceful",
        #     "version": 1
        #     },
        #     {'asset': "TRex",
        #     "sync_filename" : "Trex_texture_v003.psd",
        #     "sync_path": None,
        #     "status" : "Mad",
        #     "version": 2
        #     }
        
        # ]

        
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
        return partialclass(Ui_SyncForm, self.parent, self, logger=self.parent_sgtk_app.logger)


    def run(self):
        """
        Assumes we arent handling the UI elsewhere, and want to launch it here. 
        """
        import sys


        app = QtGui.QApplication(sys.argv)
        ui = Ui_SyncForm(self.parent, self)
        #sys.exit()
        ui.show()
        ui.render_to_image()
        app.exec_()

    # def log_error(self, e):
    #     self.fw.log_error(str(e))
    #     self.fw.log_error(traceback.format_exc())

    # def scan(self):
    #     # old storage we likely dont need. Lets find out. 
    #     self._asset_item_info = {}
    #     self._asset_items = {}
    #     self._sync_items = {}
    #     self._step_options = []

    #     self._filtered_away = []

    #     self.use_filters = ['Step', 'Type', 'Ext']
    #     self.filter_sizes = {
    #         "Step" : 80,
    #         "Type" : 130,
    #         "Ext" : 50
    #     }

        # init preferences
        # self.prefs = PrefFile()
        # if not self.prefs.data.get('hide_syncd'):
        #     self.prefs.data['hide_syncd'] = True
        #     self.prefs.write()
        #     self.prefs.read()

        # if not self.prefs.data.get('force_sync'):
        #     self.prefs.data['force_sync'] = False
        #     self.prefs.write()
        #     self.prefs.read()
        # self.threadpool = QtCore.QThreadPool.globalInstance()
        # self.threadpool.setMaxThreadCount(min(23, self.threadpool.maxThreadCount()))

        # creat UI elements and arrange them
        # self.make_widgets()
        # self.setup_ui()

        # # add assets and what we want to sync into the view
        # if self.entities_to_sync:
        #     self.populate_assets()
        # else:
        #     self._do.setVisible(False)
        #     self._asset_tree.setVisible(False)
        #     self._progress_bar.setRange(0, 1)
        #     self._progress_bar.setValue(0)
        #     self.set_progress_message("Please use Perforce Sync with a chosen context. None detected.", percentf=" ")

    # def rescan(self):
    #     self._asset_tree.clear()
    #     self.populate_assets()

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
        

    




    



   

    def update_available_filters(self, filter_info):
        """
        
        TODO: implement during scraping/transformation of data
        Populate the steps filter menu as steps are discovered in the p4 scan search
        """
        try:
            filter_type = filter_info[0]
            filter_value = filter_info[1]


            actions = getattr(self, "_{}_actions".format(filter_type))
            #if actions:
            if filter_value not in actions.keys():
                action = QtGui.QAction(self)
                
                action.setCheckable(True)

                self.prefs.read()
                filters = self.prefs.data.get('{}_filters'.format(filter_type))
                check_state = True
                if filter_value in filters.keys():
                    check_state = filters[filter_value]
                

                action.setChecked(check_state)
                action.setText(str(filter_value))
                action.triggered.connect(self.save_ui_state)
                action.triggered.connect(self.filter_items)

                getattr(self, "_{}_menu".format(filter_type)).addAction(action)
                actions[filter_value] = action

        except Exception as e:
            self.log_error(e)

  

   
    def update_view(self):
        #TODO do the actually update of ui here
        pass

    def setup(self):
        self.initialize_data()
        self.logger.info(f'App build completed with workers')

    def report_worker_info(self, item_dict):
        
        try:
            self.ui.model.add_row(item_dict)
            self.ui.reload_view()
            self.ui.set_ready(True)
        except Exception as e:
            import traceback
            self.logger.error(e)
            raise sgtk.TankError(e)
        self.logger.info("THIS CAME FROM THE EVENT" + str(item_dict))

    def initialize_data(self):
        """
        Iterate through tk-multi-perforce delivered list of asset information, 
        Utilize a global threadpool to process workers to ask P4 server for what 
        there is to sync for these. 
        """
        try:
             
            # self.asset_item_registry = {}  

            # self.sync_items = {}
            # self.sync_order = []




            # self.ui.progress = 0

            # self.ui.progress_maximum = len(self.data)
            # self.ui._progress_bar.setRange(0, self.ui.progress_maximum)
            # self.ui._progress_bar.setValue(0)
            
            
            # self.ui.set_progress_message("Requesting asset information for SG selection...")

            # self.fw.log_info(len(self.entities_to_sync))
            # iterate all parent assets

            # workers = []
            # for entity_to_sync in self.input_data:

            asset_info_gather_worker = AssetInfoGatherWorker(app=self.parent_sgtk_app,
                                                            entity=self.input_data,
                                                            framework=self.fw)

            # if self.ui._force_sync.isChecked():
            #     asset_info_gather_worker.force_sync = True



            # TODO: reconnect to working methods
            # asset_info_gather_worker.info_gathered.connect( self.asset_info_handler )

            # implement in Ui_form
            # TODO: reimplement the below
            # asset_info_gather_worker.progress.connect( self.iterate_progress )
            # asset_info_gather_worker.status_update.connect(self.set_progress_message)

            asset_info_gather_worker.item_found_to_sync.connect(self.report_worker_info)
            # asset_info_gather_worker.status_update.connect(self.set_progress_message)
            # asset_info_gather_worker.includes.connect(self.update_available_filters)

            # if hasattr(self, 'child_asset_ids'):
            #     if self.child_asset_ids:
            #         if entity_to_sync.get('id') in self.child_asset_ids:
            #             asset_info_gather_worker.child = True
            # asset_info_gather_worker.run()
            
            self.ui.threadpool.start(asset_info_gather_worker)
               


        except Exception as e:
            self.logger.error(e)


    def make_icon(self, name):
        """
        Helper to return QIcon from our limited icon schema used. 
        """
        return QtGui.QIcon(os.path.join(basepath, 'resources', "status_{}.png".format(name)))


    def sync_in_progress(self, sync_item):
        """
        TODO: 
        Handle signal from SyncWorker.started to inform user that sync has started within sync_item_widget. 
        This sync_item_widget is looked up from our global asset dictionary using the signal payload arg [dict]
        """

        asset_name = sync_item.get('asset_name')
        sync_path = sync_item.get("sync_path")

        sync_item_widget = self._asset_items[asset_name].get('child_widgets').get(sync_path)
        asset_item_widget = self._asset_items[asset_name].get('tree_widget')

        icon  = self.make_icon("syncing")
        sync_item_widget.setIcon(1, icon)
        sync_item_widget.setText(1, "Syncing")

        self._asset_tree.scrollTo(self._asset_tree.indexFromItem(sync_item_widget))
        asset_item_widget.setExpanded(True)
    

    def item_syncd(self, sync_item):
        """
        TODO: add functionality to model or item method
        Handle signal from SyncWorker.progress to display sync status in sync_item_widget. 
        This sync_item_widget is looked up from our global asset dictionary using the signal payload arg [dict]
        """

        # log status of sync for this item
        asset_name = sync_item.get('asset_name')
        sync_path = sync_item.get("sync_path")
        response = sync_item.get('response')

        # self.fw.log_debug(sync_path)

        # look up the sync-item object since we're passing only a topic/string around via signal
        child_widgets = self._asset_items[asset_name].get('child_widgets')
        sync_item_widget = child_widgets.get(sync_path)
        asset_item_widget = self._asset_items[asset_name].get('tree_widget')
        
        # since we're getting this                                                                
        icon  = self.make_icon("success")
        sync_item_widget.setIcon(1, icon)
        sync_item_widget.setText(1, "Syncd")

        # check how many asset children are still needing to be synced
        count_left_to_sync = len([sync_widget for sync_path,sync_widget in child_widgets.items() if sync_widget.text(1)=="Ready"])

        # set parent
        parent_asset_status = "{} item{} to sync"
        plurality = ""
        if count_left_to_sync > 0:
            if count_left_to_sync > 1:
                plurality = "s"

            # set asset parent's status regarding count-left-to-sync
            asset_item_widget.setText(1, parent_asset_status.format(count_left_to_sync, plurality))
        else:
            # when all sync's are done...
            icon  = self.make_icon("validate")
            asset_item_widget.setIcon(1, icon)
            asset_item_widget.setText(1,"Asset in Sync" )

        self.iterate_progress(message="Syncing {}".format(sync_item_widget.text(0)))


    def start_sync(self):
        """ 
        Iterate through assets and their sync items to start workers for all paths that require syncs. 
        Utilize a global threadpool to process
        """
        try:
            self.set_ui_interactive(False)

            workers = []
            for asset_name, asset_dict in self._asset_items.items():
                for sync_path, sync_widget in asset_dict['child_widgets'].items():
                    if not sync_widget.isHidden():
                        sync_worker = SyncWorker()
                        sync_worker.path_to_sync = sync_path
                        sync_worker.asset_name = asset_name

                        sync_worker.fw = self.fw
                        
                        sync_worker.started.connect(self.sync_in_progress)
                        # worker.finished.connect(self.sync_completed)
                        sync_worker.progress.connect(self.item_syncd)

                        workers.append(sync_worker)
                    
            self.progress = 0

            self.progress_maximum = len(workers)
            self._progress_bar.setRange(0, self.progress_maximum)
            self._progress_bar.setValue(0)
            self._progress_bar.setVisible(True)
            self._progress_bar.setFormat("%p%")

            # make threadpool to take all workers and multithread their execution
            # self.threadpool = QtCore.QThreadPool.globalInstance()
            # self.threadpool.setMaxThreadCount(min(24, self.threadpool.maxThreadCount()))

            # self.fw.log_debug("Starting Threaded P4 Sync...")

            # setup workers for multiprocessing

            for sync_worker in workers:
                sync_worker.run()
        except Exception as e:
            self.log_error(e)