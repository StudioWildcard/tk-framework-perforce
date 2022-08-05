import sgtk
from sgtk.platform.qt import QtCore, QtGui

class SortFilterModel(QtGui.QSortFilterProxyModel):
    """
    A proxy model that excludes files from the view
    that end with the given extension
    """
    def __init__(self, excludes, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._excludes = excludes[:]

    def filterAcceptsRow(self, srcRow, srcParent):
        idx = self.sourceModel().index(srcRow, 0, srcParent)
        name = idx.data()
        print("Filtered: {}".format(name))
        for i in self._excludes:
            if i in name:
                return False
        
        return True