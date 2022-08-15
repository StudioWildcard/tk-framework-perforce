import sgtk
from sgtk.platform.qt import QtCore, QtGui


class SortFilterModel(QtGui.QSortFilterProxyModel):
    """
    A proxy model that excludes files from the view
    that end with the given extension
    """

    def __init__(
        self,
        excludes,
        *args,
        parent=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._excludes = excludes[:]
        self.main_ui = parent

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
        # idx = self.sourceModel().index(srcRow, 1, srcParent)
        # item = idx.internalPointer()
        try:

            parent_item = self.sourceModel().item(srcParent)
            item = parent_item.child(srcRow)
            item.visible = True

            if hasattr(item, "primary"):
                if item.primary:

                    return True
            # # else:
            name = item.itemData[2]

            # self.main_app.logger.error(str(item.itemData))
            include = self.main_ui.utils.prefs.data.get("ext_filters")
            # self.main_app.logger.info(include)
            include_list = [k for k, v in include.items() if v is True]
            # self.main_app.logger.info(str())
            # # self.main_app.logger.info(tree_item)

            if name:
                if name not in include_list:
                    # self.main_app.logger.error("HIDIN!!!!!: {}".format(name))
                    print("Filtered: {}".format(name))
                    item.visible = False
                    return False
            return True
        except Exception as e:
            self.main_app.logger.info(e)
            return True
