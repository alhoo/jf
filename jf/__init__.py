"""Pyq python json/yaml query engine"""

import sys
import json
import logging
from datetime import datetime, timezone
from itertools import islice
from functools import reduce

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


def parse_value(val):
    """Parse value to complex types"""
    from dateutil import parser as dateutil
    try:
        if len(val) > 10:
            time = dateutil.parse(val)
        else:
            return val
        return time
    except ValueError:
        return val
    except TypeError:
        return val


class Struct:
    """Class representation of dict"""

    def __init__(self, **entries):
        self.__jf_struct_hidden_fields = ["_Struct__jf_struct_hidden_fields"]
        self.update(entries)

    def __getitem__(self, item):
        """Return item attribute if exists"""
        if item in self.__dict__:
            return self.__dict__[item]
        return None

    def dict(self):
        """Convert item to dict"""
        print("To dict", self.__jf_struct_hidden_fields)
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
                self.__dict__[key] = parse_value(val)
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


def pipelogger(arr):
    """Log pipe items"""
    for val in arr:
        logger.debug("'%s' goes through the pipeline", val)
        yield val


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
    if not isinstance(stop, int):
        stop = 1
    if len(args) > 1:
        start = stop
        stop = args[1]
    if not isinstance(stop, int):
        stop = 1
    if len(args) > 2:
        step = args[2]
    if not isinstance(step, int):
        step = 1
    return islice(arr, start, stop, step)


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
    if len(args) == 2:
        shown = args[0](arr)
    if not isinstance(shown, int):
        shown = 1
    return islice(arr, 0, shown)


def last(*args):
    """Show last (N) items"""
    arr = args[-1]
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
#        pipeline = pipelogger(pipeline)
        for fun in self._filters:
            pipeline = fun(to_struct_gen(pipeline))
        return pipeline


def query_convert(query):
    """Convert query for evaluation"""
    import regex as re
    res = {
        "fnre": r'([a-zA-Z][^()]+)',
        "argsre": r'(\([^()=]*(\(([^()]*(?3)?[^()]*)*\))?)',
        "kwargsre": r'(, [^()]+)?',
        "classfn": r'(\.[^ ]*)?',
    }
    lambdare_str = r'%s%s%s\)%s' % (res["fnre"], res["argsre"],
                                    res["kwargsre"], res["classfn"])
    lambdasub = r'lambda arr: \1(lambda x, *rest: \2), arr\5)\6'
    namere = re.compile(r'([{,] *)([^{} "\',]+):')
    makexre = re.compile(r'([ (])(\.[a-zA-Z])')
    lambdare = re.compile(lambdare_str)
    nowre = re.compile(r"NOW\(\)")
    logger.debug("Before conversion: %s", query)
    query = namere.sub(r'\1"\2":', query)
    logger.debug("After namere: %s", query)
    query = makexre.sub(r'\1x\2', query)
    logger.debug("After makex: %s", query)
#    query = lambdare.sub(r'lambda arr: \1(lambda x, *rest: \2, arr)\4', query)
    query = lambdare.sub(lambdasub, query)
    logger.debug("After Lambdare: %s", query)
    query = nowre.sub(r'datetime.now(timezone.utc)', query)
    logger.debug("After nowre: %s", query)
    query = "gp(data, [" + query + "]).process()"
    logger.debug("Final query '%s'", query)
    return query


def run_query(query, data, imports=None):
    """Run a query against given data"""
    import importlib
    query = query_convert(query)
    # To anyone reading: I'm sorry. I'm a terrible person...
    globalscope = {
        "data": data,
        "gp": GenProcessor,
        "islice": jfislice,
        "first": first,
        "last": last,
        "age": age,
        "hide": hide,
        "reduce": reduce,
        "reduce_list": reduce_list,
        "sorted": lambda x, arr, **kwargs: sorted(arr, key=x, **kwargs),
        "datetime": datetime,
        "timezone": timezone}
    if imports:
        globalscope.update({imp: importlib.import_module(imp)
                            for imp in imports.split(",")})
    try:
        res = eval(query, globalscope)
        for val in res:
            yield val
    except TypeError as ex:
        yield res
    except KeyError as ex:
        logger.warning("Got an exception while yielding results")
        logger.warning("Exception: %s", repr(ex))
        logger.warning("You might have typoed an attribute")
    except Exception as ex:
        logger.warning("Got an unexpected exception while yielding results")
        logger.warning("Exception: %s", repr(ex))
        raise
