from ..schema.schema_resolver import BaseTransformer

class SyncTransformer(BaseTransformer):
    def __init__(self) -> None:
        self._item = None

        # if you use a transformer method for heavy calculation,
        # you may intend to store
        self._cache = {}

        super().__init__()

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, item):
        self._item = item

    def sync_item(self, dict_value):
        return dict_value.get("depotFile").split("/")[-1]

    def sync_status(self, dict_value):
        if self.item:
            if hasattr(self.item, "syncing"):
                return "Syncing..."
        return dict_value

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


    def resolve(self):
        pass
        # TODO: bring concept of resolving ONLY when a row calls for column to be transformed

        #     self._serial_data = []
        #     for col in self.column_schema:

        #         val = "n/a"
        #         # cerberus match against schema

        #         if self.data_in.get(col["key"]):
        #             val = self.data_in[col["key"]]
        #             if col.get("transform"):
        #                 if self.transformers:
        #                     # give transformer access to col
        #                     self.transformers.col = self
        #                     if hasattr(self.transformers, col["transform"]):
        #                         val = getattr(self.transformers, col["transform"])(val)

        #         elif col.get("default"):
        #             val = col["default"]
        #         self._serial_data.append(val)

        #     return self._serial_data
