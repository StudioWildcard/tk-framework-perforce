from fileinput import filename
import os
import json
import webbrowser
import functools
import uuid
import traceback
import sgtk

logger = sgtk.platform.get_logger(__name__)


class PrefFile:
    def __init__(self, filename=".p4syncpref"):
        self.root_dir = os.path.expanduser("~")
        self.pref_file = os.path.join(self.root_dir, filename)

        self.read()

    def write(self, data=None):
        if not data:
            data = self.data
        with open(self.pref_file, "w") as file_obj:
            json.dump(data, file_obj, indent=4)

    def read(self):
        if not os.path.isfile(self.pref_file):
            self.data = {}
            self.write(self.data)
        with open(self.pref_file, "r") as file_obj:
            self.data = json.load(file_obj)
            return self.data


def open_browser(path):
    """
    Open file in a local file browser using file path uri
    """
    webbrowser.open("file:///" + path)


def partialclass(cls, *args, **kwds):
    class NewCls(cls):
        __init__ = functools.partialmethod(cls.__init__, *args, **kwds)

    return NewCls


def trace(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(self, *args, **kw):
        try:
            catch = fn(self, *args, **kw)
            # logger.debug(f"Function: {fn.__name__} [success]")
            return catch
        except Exception:

            logger.error(traceback.format_exc())

    return wrapper


def method_decorator(decorator):
    def decorate(cls):
        for attr in cls.__dict__:  # there's propably a better way to do this
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls

    return decorate
