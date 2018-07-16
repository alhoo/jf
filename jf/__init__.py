"""Pyq python json/yaml query engine"""

import sys
import json
import logging
from datetime import datetime, timezone
from itertools import islice, chain
from collections import deque, OrderedDict
from functools import reduce
from jf.parser import parse_query

logger = logging.getLogger(__name__)


def age(datestr):
    """Try to guess the age of datestr"""
    from dateparser import parse as parsedate
    logger.debug("Calculating the age of '%s'", datestr)
    ret = 0
    try:
        ret = datetime.now() - parsedate(str(datestr))
    except TypeError:
        ret = datetime.now(timezone.utc) - parsedate(str(datestr))
    logger.debug("Age of '%s' is %s", datestr, repr(ret))
    return ret


def peek(data, count=100):
    """Slice and memoize data head"""
    head = list(islice(data, 0, count))
    if isinstance(data, (list, tuple, dict)):
        data = islice(data, count, None)
    return head, chain(head, data)


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


class OrderedStruct:
    """Class representation of dict"""

    def __init__(self, entries):
        """
        :param entries: data used to make the ordered struct

        >>> it = OrderedStruct(OrderedDict([['a', 3], ['b', 19]]))
        >>> it.a
        3
        >>> it.dict()['b']
        19
        >>> _ = it.hide('b')
        >>> list(it.dict().keys())
        ['a']
        >>> it.c
        """
        self.__jf_struct_hidden_fields = ["_Struct__jf_struct_hidden_fields"]
        self.data = OrderedDict()
        logger.info("Filling Ordered Struct with %s", type(entries))
        logger.info("Filling Ordered Struct with %s", repr(entries))
        self.update(entries)

    def __getattr__(self, item):
        """Return item attribute if exists"""
        return self.__getitem__(item.replace("__JFESCAPED_", ''))

    def __getitem__(self, item):
        """Return item attribute if exists"""
        if item in self.data:
            return self.data[item]
        return None

    def dict(self):
        """Convert item to dict"""
        return OrderedDict([(k, v) for k, v in self.data.items()
                if k not in self.__jf_struct_hidden_fields])

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
                for k3, v3 in flatten_item(v2, key+'.%d.' % idx).items():
                    ret[k3] = v3
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
    try:
        for it in map(result_cleaner, arr):
            yield flatten_item(it)
    except TypeError as err:
        logger.error("Got an value error while flattening dict %s", err)


def result_cleaner(val):
    """Cleanup the result
    >>> result_cleaner({'a': 1})
    {'a': 1}
    >>> from pprint import pprint
    >>> pprint(result_cleaner(OrderedStruct(OrderedDict([['b', 1], ['a', 2]]))))
    OrderedDict([('b', 1), ('a', 2)])
    """
    if isinstance(val, OrderedStruct):
        return json.loads(json.dumps(val.data, cls=StructEncoder),
                         object_pairs_hook=OrderedDict)
    return json.loads(json.dumps(val, cls=StructEncoder))


def excel(*args, **kwargs):
    """Convert input to excel
    >>> excel(lambda x: "/tmp/excel.xlsx", [{'a': 1}, {'a': 3}])
    Traceback (most recent call last):
      File "/usr/lib/python3.5/doctest.py", line 1321, in __run
        compileflags, 1), test.globs)
      File "<doctest jf.excel[0]>", line 1, in <module>
        excel(lambda x: "/tmp/excel.xlsx", [{'a': 1}, {'a': 3}])
      File "/home/lasse/Desktop/programming/jf/jf/__init__.py", line 298, in excel
        raise StopIteration()
    StopIteration: All results written
    """
    import pandas as pd
    arr = args[-1]
    if len(args) > 1:
        args = [args[0](0)]
    else:
        args = ['-']
    logger.info("Writing excel with args: %s and kwargs: %s", args, kwargs)
    writer = pd.ExcelWriter(*args, **kwargs)
    df = pd.DataFrame(list(map(result_cleaner, arr)))
    df.to_excel(writer)
    writer.save()
    raise StopIteration("All results written")


def profile(*args, **kwargs):
    """
    Make a profiling report from data

    This function tries to convert strings to numeric values or datetime
    objects and makes a html profiling report as the only result to be yielded.
    Notice! This fails if used with ordered_dict output.

    >>> list(map(lambda x: len(x) > 100, profile([{'a': 1}, {'a': 3}, {'a': 4}])))
    [True]
    """
    import pandas as pd
    import pandas_profiling

    def is_numeric(df_):
        try:
            counts = df_.value_counts()
            if len(counts) > 100:
                pd.to_numeric(df.value_counts()[4:24].keys())
            else:
                pd.to_numeric(df.value_counts().keys())
            return True
        except (ValueError, AttributeError):
            pass
        return False

    arr = args[-1]
    if len(args) > 1:
        args = [open(args[0](0), 'w')]
    else:
        args = []
    data = list(map(result_cleaner, arr))
    df = pd.DataFrame(data)
    na_value = None
    if 'nan' in kwargs:
        na_value = kwargs['nan']
    for col in df.columns:
        try:
            if is_numeric(df[col]):
                if na_value:
                    df[col] = df[col].str.replace(na_value, None)
                df[col] = pd.to_numeric(df[col].str.replace(",", '.'), errors='coerce')
            else:
                df[col] = pd.to_datetime(df[col].str.replace(",", '.'))
        except (AttributeError, KeyError, ValueError):
            pass
    profile_data = pandas_profiling.ProfileReport(df)
    html_report = pandas_profiling.templates.template('wrapper').render(content=profile_data.html)
    if len(args):
        args[0].write(html_report+"\n")
    else:
        yield html_report
    raise StopIteration()


def browser(*args, **kwargs):
    import webbrowser
    import tempfile
    import time
    arr = args[-1]
    with tempfile.NamedTemporaryFile('w') as f:
        for line in arr:
            f.write(line)
        webbrowser.open(f.name)
        time.sleep(1)  # Hack to give the browser some time


def md(*args, **kwargs):
    from csvtomd import md_table
    from math import isnan
    arr = args[-1]
    if len(args) > 1:
        args = [open(args[0](0), 'w')]
    else:
        args = []
    table = []
    first = True
    for row in map(result_cleaner, arr):
        logger.info("Writing row %s", row)
        if first:
            table.append([str(v) if v else '' for v in row.keys()])
            first = False
        table.append([str(v) if isinstance(v, str) or not isnan(v) else '' for v in row.values()])
    if len(args):
        args[0].write(md_table(table)+"\n")
    else:
        print(md_table(table))
    raise StopIteration()


def csv(*args, **kwargs):
    import csv
    arr = args[-1]
    if len(args) > 1:
        args = [open(args[0](0), 'w')]
    else:
        args = [sys.stdout]
    r = csv.writer(*args, **kwargs)
    first = True
    for row in map(result_cleaner, arr):
        logger.info("Writing row %s", row)
        if first:
            r.writerow(row.keys())
            first = False
        r.writerow(row.values())
    raise StopIteration()


def ipy(banner, data, fakerun=False):
    """Start ipython with data-variable"""
    from IPython import embed
    if not isinstance(banner, str):
        banner = ''
    banner += '\nJf instance is now dropping into IPython\n'
    banner += 'Your filtered dataset is loaded in a iterable variable '
    banner += 'named "data"\n\ndata sample:\n'
    head, data = peek(map(result_cleaner, data), 1)
    if head:
        banner += json.dumps(head[0], indent=2, sort_keys=True)
    banner += "\n\n"
    if not fakerun:
        embed(banner1=banner)


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


def unique(*args):
    """Calculate unique according to function"""
    if len(args) > 1:
        fun = args[0]
    else:
        fun = lambda x: repr(x)
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
    logger.info("Using hide-pipeline")
    for item in arr:
        item.hide(elements(item))
        yield item


def firstnlast(*args):
    """Show first and last (N) items"""
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
        val.__dict__.update(fun(val))
        yield val


class OrderedGenProcessor:
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


RED = "\033[1;31m"
BLUE = "\033[1;34m"
CYAN = "\033[1;36m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD = "\033[;1m"
REVERSE = "\033[;7m"


def colorize(ex):
    """Colorize syntax error"""
    if not isinstance(ex.args, (list, tuple)):
        return repr(ex.args)
    if not isinstance(ex.args[1], (list, tuple)):
        return repr(ex.args)
    string = [c for c in ex.args[1][3]]
    start = ex.args[1][2]-ex.args[1][1]
    stop = ex.args[1][2]
    string[start] = RED+string[start]
    if stop >= len(string):
        string.append(RESET)
    else:
        string[stop] = RESET+string[stop]
    return ''.join(string)


def query_convert(query):
    """Convert query for evaluation"""
    import regex as re
    indentre = re.compile(r'\n *')
    namere = re.compile(r'([{,] *)([^{} "\[\]\',]+):')
    firstxre = re.compile(r'^(\.[a-zA-Z])')
    makexre = re.compile(r'([ (])(\.[a-zA-Z])')
    keywordunpackingre = re.compile(r'\( *\*\*x *\)')
    nowre = re.compile(r"NOW\(\)")
    logger.debug("Before conversion: %s", query)
    query = indentre.sub(r' ', query)
    logger.debug("After indent removal: %s", query)
    query = namere.sub(r'\1"\2":', query)
    logger.debug("After namere: %s", query)
    query = firstxre.sub(r'x\1', query)
    query = makexre.sub(r'\1x\2', query)
    logger.debug("After makex: %s", query)
    query = keywordunpackingre.sub('(**x.dict())', query)
    logger.debug("After kw-unpacking: %s", query)
    try:
        jfkwre = re.compile(r'\.([a-z]+[.)><\!=, ])')
        query = jfkwre.sub(r'.__JFESCAPED_\1', query)
        logger.debug("Parsing: '%s'", query)
        query = parse_query(query).rstrip(",")
    except (TypeError, SyntaxError) as ex:
        logger.warning("Syntax error in query: %s", repr(ex.args[0]))
        query = colorize(ex)
        ijfkwre = re.compile(r'\.__JFESCAPED_([a-z]+[.)><\!=, ])')
        query = ijfkwre.sub(r'.\1', query)
        sys.stderr.write("Error in query:\n\t%s\n\n" % query)
        raise StopIteration
    logger.debug("After query parse: %s", query)
    query = nowre.sub(r'datetime.now(timezone.utc)', query)
    logger.debug("After nowre: %s", query)
    query = "gp(data, [" + query + "]).process()"
    logger.debug("Final query '%s'", query)
    return query


def run_query(query, data, imports=None, import_from=None, ordered_dict=False):
    """Run a query against given data"""
    import regex as re
    query = query_convert(query)

    globalscope = {
        "data": data,
        "gp": GenProcessor,
        "islice": jfislice,
        "head": first,
        "update": update,
        "tail": last,
        "first": first,
        "firstnlast": firstnlast,
        "headntail": firstnlast,
        "last": last,
        "null": None,
        "I": lambda arr: arr,
        "age": age,
        "re": re,
        "date": parse_value,
        "hide": hide,
        "unique": unique,
        "ipy": ipy,
        "csv": csv,
        "md": md,
        "browser": browser,
        "profile": profile,
        "excel": excel,
        "flatten": flatten,
        "reduce": reduce,
        "reduce_list": reduce_list,
        "yield_all": yield_all,
        "yield_from": yield_all,
        "group": reduce_list,
        "chain": reduce_list,
        "sorted": lambda x, arr=None, **kwargs: sorted(arr, key=x, **kwargs),
        "datetime": datetime,
        "timezone": timezone}
    if imports:
        import importlib
        import os
        sys.path.append(os.path.dirname('.'))
        if import_from:
            sys.path.append(os.path.dirname(import_from))
        globalscope.update({imp: importlib.import_module(imp)
                            for imp in imports.split(",")})

    if ordered_dict:
        globalscope["gp"] = OrderedGenProcessor

    try:
        res = eval(query, globalscope)
        for val in res:
            yield val
    except (ValueError, TypeError) as ex:
        logger.warning("Exception: %s", repr(ex))
