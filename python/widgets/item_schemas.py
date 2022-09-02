import sgtk
from sgtk.platform.qt import QtCore, QtGui
from ..schema import Schema
from .sync_transformers import SyncTransformer

logger = sgtk.platform.get_logger(__name__)

schema = Schema(template_schema=None)
transformer = SyncTransformer(schema=None)

class Row:
    def __init__(self, data,  parent=None):
        self.childItems = []
        self.data_in = data
        self.parentItem = parent

        self.transformer = transformer


        self.visible = True
        if parent:
            parent.appendChild(self)


        self._cached_data = []
        # self._col_map = [i.get('key') for i in schema]
        self.primary = primary

        # how we will render our data to the model
        self._serial_data = []

        self.schema = schema
        # self.transformers = transformers
        # self.transformers = Transformers()

        # if schema:
        #     if schema in self.schemas.keys():
        #self.schema.schema = self.schemas[schema]
        # else:
        #     raise Exception("Schema-driven items require a schema to reference.")

        if not data:
            data = {"name": "None"}

    @property
    def itemData(self):
        # self.transformer.item = self
        # value = original
        # for i in schema_columns:
        #     if i should translate:
        #         append(translated)
        #     else:
        #         value
        # return self.transformer.resolve()

        for col in self.schema.schema:

            val = "n/a"
            # cerberus match against schema

            if self.data_in.get(col["key"]):
                val = self.data_in[col["key"]]
                if col.get("transform"):
                    if self.transformers:
                        # give transformer access to col
                        self.transformers.col = self
                        if hasattr(self.transformers, col["transform"]):
                            val = getattr(self.transformers, col["transform"])(val)

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

    ## Schema refactor into row as component of row VVVVV

    def header_data(self, index):
        return self.schema.schema[index].get("title")

    def set_data(self, index, value):
        self.data_in[self._col_map[index]] = value

    @property
    def _col_map(self):
        return [i.get("key") for i in self.schema.schema]


# class RowSchema(Row):
#     def __init__(
#         self,
#         data=None,
#         schema=None,
#         parent=None,
#         primary=False,
#         transformers=None,
#         **kwargs
#     ):


#         super().__init__(data=data, parent=parent, **kwargs)






