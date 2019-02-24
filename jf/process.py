"""Pyq python json/yaml query engine"""

import logging
from datetime import datetime, timezone
from itertools import islice
from collections import deque, OrderedDict
from jf.output import result_cleaner
from jf.meta import to_struct_gen

logger = logging.getLogger(__name__)


def age(datestr):
    """Try to guess the age of datestr"""
    from dateparser import parse as parsedate
    logger.debug("Calculating the age of '%s'", datestr)
    try:
        ret = datetime.now() - parsedate(str(datestr))
    except TypeError:
        ret = datetime.now(timezone.utc) - parsedate(str(datestr))
    logger.debug("Age of '%s' is %s", datestr, repr(ret))
    return ret


def parse_value(val):
    """Parse value to complex types"""
    logger.debug("Parsing date from '%s'", val)
    from dateutil import parser as dateutil
    try:
        if len(val) > 1:
            time = dateutil.parse(val)
        else:
            return val
        logger.debug("Got time '%s'", time)
        return time
    except ValueError as ex:
        logger.debug("Not a date k7j5 value: %s", val)
        logger.info(ex)
        return val


def jfislice(*args):
    """jf wrapper for itertools.islice"""
    arr = args[-1]
    args = args[0](0)
    start = None
    step = None
    stop = 1
    if isinstance(args, int):
        args = [args]
    if args:
        stop = args[0]
    if len(args) > 1:
        start = stop
        stop = args[1]
    if len(args) > 2:
        step = args[2]
    return islice(arr, start, stop, step)


def flatten_item(it, root=''):
    """
    Make item flat
    :param it: item
    :param root: root node
    :return: flattened version of the item
    >>> flatten_item("foo")
    'foo'
    >>> flatten_item({"a": 1})
    {'a': 1}
    >>> from pprint import pprint
    >>> pprint(flatten_item({"a": 1, "b":{"c":2}}))
    {'a': 1, 'b.c': 2}
    >>> list(sorted(flatten_item({"a": 1, "b":{"c":2}}).items()))
    [('a', 1), ('b.c', 2)]
    >>> list(sorted(flatten_item({"a": 1, "b":[1,2]}).items()))
    [('a', 1), ('b.0', 1), ('b.1', 2)]
    """
    if not isinstance(it, dict):
        return it
    ret = {}
    logger.info("Flattening %s", it)
    for key, val in it.items():
        logger.info("%s: %s", key, val)
        if isinstance(val, dict):
            for k2, v2 in flatten_item(val, key+'.').items():
                ret[k2] = v2
        elif isinstance(val, list):
            for idx, v2 in enumerate(val):
                dct2 = flatten_item(v2, key+'.%d.' % idx)
                if isinstance(dct2, dict):
                    for k3, v3 in dct2.items():
                        ret[k3] = v3
                else:
                    ret[key+".%d" % idx] = dct2
        else:
            ret[root+key] = val
    logger.debug("Flattening %s => %s", it, ret)
    return ret


def flatten(*args):
    """
    Flatten array
    :param args: array to flatten
    :return: array of flattened items
    >>> from pprint import pprint
    >>> pprint(list(flatten([{'a': 1, 'b':{'c': 2}}])))
    [{'a': 1, 'b.c': 2}]
    """
    logger.info("Flattening")
    arr = args[-1]
    for it in map(result_cleaner, arr):
        yield flatten_item(it)


def transpose(*args):
    """ Transpose input
    >>> data = [{'a': 1, 'b': 2}, {'a': 2, 'b': 3}]
    >>> arr = to_struct_gen(data)
    >>> list(sorted(map(lambda x: list(x.items()), transpose(arr)), key=lambda x: x[0][1]))
    [[(0, 1), (1, 2)], [(0, 2), (1, 3)]]
    """
    import pandas as pd
    arr = args[-1]
    data = [x.dict() for x in arr]
    df = pd.DataFrame(data)
    for it in df.to_dict(into=OrderedDict).values():
        yield it


def reduce_list(*args):
    """Reduce array to a single list"""
    ret = []
    for val in args[-1]:
        ret.append(val)
    return [ret]


def yield_all(fun, arr):
    """Yield all subitems of all item"""
    for items in arr:
        for val in fun(items):
            yield val


def group_by(fun, arr):
    """Group items by value
    >>> arr = [{'item': '1', 'v': 2},{'item': '2', 'v': 3},{'item': '1', 'v': 3}]
    >>> list(sorted(map(lambda x: len(x['items']), group_by(lambda x: x['item'], arr))))
    [1, 2]
    """
    ret = {}
    for item in arr:
        val = fun(item)
        if val in ret:
            ret[val].append(item)
        else:
            ret[val] = [item]
    for k, v in ret.items():
        yield {"key": k, "items": v}


def unique(*args):
    """Calculate unique according to function"""
    if len(args) > 1:
        fun = args[0]
    else:
        # fun = lambda x: repr(x)
        def fun(x):
            return repr(x)
    seen = set()
    for it in args[-1]:
        h = hash(fun(it))
        if h in seen:
            continue
        else:
            seen.add(h)
            yield it


def hide(elements, arr):
    """Hide elements from items"""
    for item in arr:
        item.hide(elements(item))
        yield item


def firstnlast(*args):
    """Show first and last (N) items
    >>> firstnlast(lambda x: 2, [1,2,3,4,5])
    [[1, 2], [4, 5]]
    """
    arr = args[-1]
    shown = 1
    if len(args) == 2:
        shown = args[0](arr)
    if not isinstance(shown, int):
        shown = 1
    return [list(islice(arr, 0, shown)), list(iter(deque(arr, maxlen=shown)))]


def first(*args):
    """Show first (N) items"""
    arr = args[-1]
    shown = 1
    if len(args) == 2:
        shown = args[0](arr)
    if not isinstance(shown, int):
        shown = 1
    return islice(arr, 0, shown)


def last(*args):
    """Show last (N) items"""
    arr = args[-1]
    shown = 1
    if len(args) == 2:
        shown = args[0](arr)
    if not isinstance(shown, int):
        shown = 1
    return iter(deque(arr, maxlen=shown))
    # list(arr)[-shown:]


def update(fun, arr):
    """update all items using function"""
    for val in arr:
        if val.data is not None:
            val.data.update(fun(val))
        else:
            val.update(fun(val))
        yield val


class OrderedGenProcessor:
    """Make a generator pipeline"""

    def __init__(self, igen, filters):
        """Initialize item processor
        >>> gp = OrderedGenProcessor(['a','21','3'], [lambda arr: map(len, arr)])
        >>> gp.add_filter(lambda arr: filter(lambda x: x > 1, arr))
        >>> list(gp.process())
        [2]
        """
        self.igen = igen
        self._filters = filters

    def add_filter(self, fun):
        """Add filter to pipeline"""
        self._filters.append(fun)

    def process(self):
        """Process items"""
        pipeline = self.igen
        for fun in self._filters:
            pipeline = fun(to_struct_gen(pipeline, ordered_dict=True))
        return pipeline


class GenProcessor:
    """Make a generator pipeline"""

    def __init__(self, igen, filters):
        """Initialize item processor"""
        self.igen = igen
        self._filters = filters

    def add_filter(self, fun):
        """Add filter to pipeline"""
        self._filters.append(fun)

    def process(self):
        """Process items"""
        pipeline = self.igen
        for fun in self._filters:
            pipeline = fun(to_struct_gen(pipeline))
        return pipeline
