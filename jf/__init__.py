"""Pyq python json/yaml query engine"""

import sys
import json
import logging
from datetime import datetime, timezone
from itertools import islice, chain
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


class Struct:
    """Class representation of dict"""

    def __init__(self, **entries):
        self.__jf_struct_hidden_fields = ["_Struct__jf_struct_hidden_fields"]
        self.update(entries)

    def __getattr__(self, item):
        """Return item attribute if exists"""
        return self.__getitem__(item)

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


def to_struct(val):
    """Convert v to a class representing v"""
    if isinstance(val, dict):
        return Struct(**val)
    if isinstance(val, list):
        return [to_struct(a) for a in val]
    return val


def to_struct_gen(arr):
    """Convert all items in arr to struct"""
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
    if len(args) > 0:
        stop = args[0]
    if len(args) > 1:
        start = stop
        stop = args[1]
    if len(args) > 2:
        step = args[2]
    return islice(arr, start, stop, step)


def result_cleaner(val):
    """Cleanup the result"""
    return json.loads(json.dumps(val, cls=StructEncoder))


def ipy(banner, data, fakerun=False):
    from IPython import embed
    if not isinstance(banner, str):
        banner = ''
    banner += '\nJf instance is now dropping into IPython\n'
    banner += 'Your filtered dataset is loaded in a iterable variable '
    banner += 'named "data"\n\ndata sample:\n'
    head, data = peek(map(result_cleaner, data), 1)
    if len(head) > 0:
        banner += json.dumps(head[0], indent=2, sort_keys=True)
    banner += "\n\n"
    if not fakerun:
        embed(banner1=banner)


def reduce_list(_, arr):
    """Reduce array to a single list"""
    ret = []
    for val in arr:
        ret.append(val)
    return [ret]


def hide(elements, arr):
    """Hide elements from items"""
    logger.info("Using hide-pipeline")
    for item in arr:
        item.hide(elements(item))
#        try:
#            item.hide(items(item))
#        except Exception as ex:
#            logger.warning("Got an exception while hiding")
#            logger.warning("Exception %s", repr(ex))
        yield item


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
    return list(arr)[-shown:]


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
    namere = re.compile(r'([{,] *)([^{} "\',]+):')
    makexre = re.compile(r'([ (])(\.[a-zA-Z])')
    nowre = re.compile(r"NOW\(\)")
    logger.debug("Before conversion: %s", query)
    query = indentre.sub(r' ', query)
    logger.debug("After indent removal: %s", query)
    query = namere.sub(r'\1"\2":', query)
    logger.debug("After namere: %s", query)
    query = makexre.sub(r'\1x\2', query)
    logger.debug("After makex: %s", query)
    # from jf.parser import reparser
    # q2 = query
    # reparser(q2)
    try:
        query = parse_query(query).rstrip(",")
    except SyntaxError as ex:
        logger.warning("Syntax error in query: %s", repr(ex.args[0]))
        sys.stderr.write("Error in query:\n\t%s\n\n" % colorize(ex))
        raise
    logger.debug("After query parse: %s", query)
    query = nowre.sub(r'datetime.now(timezone.utc)', query)
    logger.debug("After nowre: %s", query)
    query = "gp(data, [" + query + "]).process()"
    logger.debug("Final query '%s'", query)
    return query


def run_query(query, data, imports=None):
    """Run a query against given data"""
#    try:
        # query = simple_query_convert(query)
    query = query_convert(query)
#    except SyntaxError:
#        return []
    # print("List of known functions")
    # functiontypes = (type(map), type(json), type(print), type(run_query))
    # isfunctypes = isinstance(x[1], functiontypes)
    # isfunction = lambda x: x[0][0] != '_' and isfunctype
    # global_functions = filter(functypes, globals().items())
    # funcs = map(lambda x: (x[0], repr(type(x[1]))), global_functions)
    # print(json.dumps(list(funcs), indent=2))
    globalscope = {
        "data": data,
        "gp": GenProcessor,
        "islice": jfislice,
        "first": first,
        "null": None,
        "last": last,
        "I": lambda arr: arr,
        "age": age,
        "date": parse_value,
        "hide": hide,
        "ipy": ipy,
        "reduce": reduce,
        "reduce_list": reduce_list,
        "sorted": lambda x, arr=None, **kwargs: sorted(arr, key=x, **kwargs),
        "datetime": datetime,
        "timezone": timezone}
    if imports:
        import importlib
        import os
        sys.path.append(os.path.dirname('.'))
        globalscope.update({imp: importlib.import_module(imp)
                            for imp in imports.split(",")})
    res = eval(query, globalscope)
    for val in res:
        yield val
