import json
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)


class JFTransformation:
    """
    Baseclass for JF transformations
    """

    def __init__(self, *args, fn=None, **kwargs):
        self.args = [
            x.replace("__JFESCAPED__", "") if isinstance(x, str) else x for x in args
        ]
        self.gen = False
        self.kwargs = kwargs
        if fn is not None:
            self._fn = fn

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None, gen=False, **kwargs):
        self.gen = gen
        return self._fn(X, **kwargs)


class Struct:
    """Class representation of dict"""

    def __init__(self, **entries):
        self.__jf_struct_hidden_fields = ["_Struct__jf_struct_hidden_fields"]
        self.update(entries)

    def __getattr__(self, item):
        """Return item attribute if exists"""
        return self.__getitem__(item.replace("__JFESCAPED_", ""))

    def __getitem__(self, item):
        """Return item attribute if exists"""
        if item in self.__dict__:
            return self.__dict__[item]
        return None

    def dict(self):
        """Convert item to dict"""
        return {
            k: v
            for k, v in self.__dict__.items()
            if k not in self.__jf_struct_hidden_fields
        }

    def hide(self, dct):
        """Mark item attribute as hidden"""
        if isinstance(dct, (list, set, tuple)):
            self.__jf_struct_hidden_fields.extend(dct)
        else:
            self.__jf_struct_hidden_fields.append(dct)
        return self

    def update(self, dct):
        """Update item with key/values from a dict"""
        for key, val in dct.items():
            if isinstance(val, (list, dict)):
                self.__dict__[key] = to_struct(val)
            else:
                self.__dict__[key] = val  # parse_value(val)
        return self


def to_struct(val):
    """Convert v to a class representing v"""
    if isinstance(val, dict):
        return Struct(**val)
    if isinstance(val, list):
        return [to_struct(a) for a in val]
    return val


def to_struct_gen(arr, ordered_dict=False):
    """Convert all items in arr to struct"""
    if ordered_dict:
        pass
    return (to_struct(a) for a in arr)


class StructEncoder(json.JSONEncoder):
    """Try to convert everything to json"""

    def default(self, obj):
        try:
            return obj.dict()
        except AttributeError:
            try:
                return obj.__dict__
            except AttributeError:
                return obj.__str__()
