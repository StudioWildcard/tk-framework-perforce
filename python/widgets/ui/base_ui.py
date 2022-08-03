from inspect import trace
from sgtk.platform.qt import QtCore, QtGui
import traceback
import logging


class Ui_Generic(QtGui.QWidget):
  
    def __init__(self, parent, logger=None):
        """
        Construction of sync UI
        """
        super().__init__(parent)

        self.parent = parent

        self._logger = logger

        self._enabled_state_toggle_widgets = []

        self.construct_widget()


    @property    
    def logger(self):
        if not self._logger:
            self._logger = logging.getLogger("genui")
        return self._logger
    
    
    def make_widgets(self):
        """
        Main function to implement to build the widget components. 
        
        Reimplement to customize your available widgets.
        """
        self._button = QtGui.QPushButton("Nexodus Generic UI Template")

    def make_layouts(self):
        """
        Main function to make the layout of the entire widget
        """
        self.main_layout = QtGui.QVBoxLayout()

    def setup_ui(self):
        """
        Main function to setup the Ui components in their layouts
        """
        self.main_layout.addWidget(self._button)

        self.setLayout(self.main_layout)

    def setup_events(self):
        """
        Main function to setup the event connections
        """
        self.logger.info("We don't have event connections implemented in this UI.")
        return None

    def construct_widget(self):
        try:
            self.make_widgets()
            self.make_layouts()

            self.setup_ui()
            self.setup_events()

            self.logger.info("Base NEXODUS Qt Widget Constructed...")
            raise Exception('derp')
        except Exception as e:
            self.logger.error(traceback.format_exc())

    def _centrally_control_enabled_state(self, widget):
        """
        Allows a widget argument to be added to a list that will be called when 
        enabling or disabling the global widget

        Args:
            widget (QWidget instance): QWidget that is desired for setting enable state_
        """
        if isinstance(widget, QtGui.QWidget):
            self._enabled_state_toggle_widgets.append(widget) 

    def set_ui_interactive(self, state):
        """
        Common utility to lock the UI while info-gathering or syncing is occuring
        """
        # toggle the installed filters

        for widget in self._enabled_state_toggle_widgets:
            widget.setEnabled(state)
