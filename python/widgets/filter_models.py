import sgtk
from sgtk.platform.qt import QtCore, QtGui


class SortFilterModel(QtGui.QSortFilterProxyModel):
    """
    A proxy model that excludes files from the view
    that end with the given extension
    """

    def __init__(self, excludes, *args, parent=None, **kwargs, ):
        super().__init__(*args, **kwargs)
        self._excludes = excludes[:]
        self.main_app = parent

    def filterAcceptsRow(self, srcRow, srcParent) -> bool:
        """
        When asked if a given row is to be filtered or remain,
        use logic to decide and return true/false for the whole
        row.

        Args:
            srcRow (_type_): _description_
            srcParent (_type_): _description_

        Returns:
            bool: True if row is to remain, False if to be filtered
        """
        idx = self.sourceModel().index(srcRow, 1, srcParent)
        name = idx.data()
        
        include = self.main_app.utils.prefs.data.get('ext_filters')
        include_list = [k for k,v in include.items() if v==True]
        self.main_app.logger.info(name )
        if name:
            if name not in include_list:
                print("Filtered: {}".format(name))
                return False


        return True
