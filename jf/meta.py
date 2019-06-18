import json
import logging
from collections import OrderedDict
logger = logging.getLogger(__name__)


class OrderedStruct:
    """Class representation of dict"""

    def __init__(self, entries):
        """
        :param entries: data used to make the ordered struct

        >>> it = OrderedStruct(OrderedDict([('a', 3), ('b', 19)]))
        >>> it.a
        3
        >>> it.dict()['b']
        19
        >>> _ = it.hide('b')
        >>> list(it.dict().keys())
        ['a']
        >>> it.c
        >>> _ = it.hide(['b', 'a'])
        >>> list(it.dict().keys())
        []
        """
        self.__jf_struct_hidden_fields = ["_Struct__jf_struct_hidden_fields"]
        self.data = OrderedDict()
        logger.info("Filling Ordered Struct with %s", type(entries))
        logger.info("Filling Ordered Struct with %s", repr(entries))
        self.update(entries)

    def __getattr__(self, item):
        """Return item attribute if exists"""
        try:
            return self.__getitem__(item.replace("__JFESCAPED_", ''))
        except KeyError:
            try:
                return OrderedStruct([[k, v] for k,v in self.items() if k.startswith(item)])
            except:
                pass

    def __getitem__(self, item):
        """Return item attribute if exists"""
        if item in self.data:
            return self.data[item]
        return None

    def dict(self):
        """Convert item to dict"""
        return OrderedDict([(k, v) for k, v in self.data.items()
                            if k not in self.__jf_struct_hidden_fields])

    def items(self):
        return self.dict().items()

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
                self.data[key] = to_ordered_struct(val)
            else:
                self.data[key] = val  # parse_value(val)
        return self


class Struct:
    """Class representation of dict"""

    def __init__(self, **entries):
        self.__jf_struct_hidden_fields = ["_Struct__jf_struct_hidden_fields"]
        self.update(entries)

    def __getattr__(self, item):
        """Return item attribute if exists"""
        return self.__getitem__(item.replace("__JFESCAPED_", ''))

    def __getitem__(self, item):
        """Return item attribute if exists"""
        if item in self.__dict__:
            return self.__dict__[item]
        return None

    def dict(self):
        """Convert item to dict"""
        return {k: v for k, v in self.__dict__.items()
                if k not in self.__jf_struct_hidden_fields}

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


def to_ordered_struct(val):
    """Convert v to a class representing v
    >>> arr = list(to_ordered_struct([{'a': 1}, {'a': 3}]))
    >>> arr[0].a
    1
    """
    logger.info("Converting %s to ordered struct", type(val))
    if isinstance(val, OrderedDict):
        return OrderedStruct(val)
    if isinstance(val, dict):
        return OrderedStruct(val)
    if isinstance(val, list):
        return [to_ordered_struct(a) for a in val]
    return val


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
        logger.info("Converting array to ordered stucts")
        return (to_ordered_struct(x) for x in arr)
    return (to_struct(x) for x in arr)


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
