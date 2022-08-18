import sgtk
from sgtk.platform.qt import QtCore, QtGui

logger = sgtk.platform.get_logger(__name__)

schemas = {
    "sync_item_schema": [
        {
            "key": "item_found",
            "title": "Name",
            "default": "No name",
            "delegate": None,
            "transform": "sync_item",
            "width": 200,
        },
        {
            "key": "status",
            "title": "Descr",
            "default": "No Description",
            "icon_finder": "sync_status",
            "width": 140,
        },
        {
            "key": "ext",
            "title": "Extension",
            "default": "No Description",
            "width": 50,
        },
        {
            "key": "item_found",
            "title": "Version",
            "default": " ",
            "transform": "revision",
        },
        {
            "key": "item_found",
            "title": "Size (MB)",
            "default": " ",
            "transform": "file_size",
        },
        {
            "key": "item_found",
            "title": "Destination",
            "default": " ",
            "transform": "destination_path",
        },
    ],
    "asset_item_schema": [
        {
            "key": "asset_name",
            "title": "Name",
            "transform": "asset_name",
            "default": "No name",
            "icon": "Shot",
        },
        {
            "key": "status",
            "title": "Descr",
            "default": "No Description",
            "transform": "total_to_sync",
            "icon_finder": "asset_status",
        },
        {"key": "_", "title": "Extension", "default": " "},
        {
            "key": "_",
            "title": "Revision",
            "default": """ """,
        },
        {
            "key": "_",
            "title": "Size (MB)",
            "default": """ """,
        },
        {
            "key": "_",
            "title": "Destination Path",
            "default": """ """,
        },
    ],
}


class Transformers:
    def __init__(self) -> None:
        self._item = None

        # if you use a transformer method for heavy calculation,
        # you may intend to store
        self._cache = {}

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, item):
        self._item = item

    def sync_item(self, dict_value):
        return dict_value.get("depotFile").split("/")[-1]

    def asset_name(self, dict_value):
        count = 0
        if self.item:
            count = self.item.childCount()
        if count:
            return dict_value + " ({})".format(count)
        return dict_value

    def total_to_sync(self, dict_value):
        items = 0
        if self.item:
            items = self.item.childCount()
        filtered = items - self.item.visible_children()
        msg = "{} To Sync".format(items - filtered)

        if filtered:
            msg += " ({} filtered)".format(filtered)

        return msg

    def revision(self, dict_value):
        return dict_value.get("rev")

    def destination_path(self, dict_value):
        return dict_value.get("clientFile")

    def file_size(self, dict_value):
        size = dict_value.get("fileSize")
        if size:
            return "{:.2f}".format(int(size) / 1024 / 1024)


class Row:
    def __init__(self, data, parent=None):
        self.childItems = []
        self.data_in = data
        self.parentItem = parent

        self.visible = True
        if parent:
            parent.appendChild(self)

    @property
    def itemData(self):
        return list(self.data_in.keys())

    def visible_children(self):
        return len([i for i in self.childItems if i.visible])

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def column(self):
        return self.columnCount()

    def isValid(self):
        return True

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

        # this runs in the model

    def parent(self):
        return self.parentItem

    def row(self):
        if hasattr(self, "primary"):
            if not self.primary:
                if self.parentItem:
                    return self.parentItem.childItems.index(self) + 1

        return 0


class RowSchema(Row):
    def __init__(
        self,
        data=None,
        schema=None,
        parent=None,
        primary=False,
        transformers=None,
        **kwargs
    ):
        self._cached_data = []
        # self._col_map = [i.get('key') for i in schema]
        self.primary = primary

        # how we will render our data to the model
        self._serial_data = []

        self.schemas = schemas

        self.transformers = transformers
        self.transformers = Transformers()

        if schema:
            if schema in self.schemas.keys():
                self.column_schema = self.schemas[schema]
        else:
            raise Exception("Schema-driven items require a schema to reference.")

        if not data:
            data = {"name": "None"}

        super().__init__(data=data, parent=parent, **kwargs)

    def header_data(self, index):
        return self.column_schema[index].get("title")

    def set_data(self, index, value):
        self.data_in[self._col_map[index]] = value

    @property
    def _col_map(self):
        return [i.get("key") for i in self.column_schema]

    @property
    def itemData(self):
        self._serial_data = []
        for item in self.column_schema:

            val = "n/a"
            # cerberus match against schema

            if self.data_in.get(item["key"]):
                val = self.data_in[item["key"]]
                if item.get("transform"):
                    if self.transformers:
                        # give transformer access to item
                        self.transformers.item = self
                        if hasattr(self.transformers, item["transform"]):
                            val = getattr(self.transformers, item["transform"])(val)

            elif item.get("default"):
                val = item["default"]
            self._serial_data.append(val)

        return self._serial_data
