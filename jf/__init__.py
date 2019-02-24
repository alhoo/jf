"""Pyq python json/yaml query engine"""

import sys
import logging
from datetime import datetime, timezone
from functools import reduce
from jf.parser import parse_query
import jf.process as process
import jf.output as output

logger = logging.getLogger(__name__)


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
    """Convert query for evaluation

    >>> cmd = 'map({id: x.a, data: x.b.d'
    >>> query_convert(cmd)
    """
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
        # raise SyntaxError
        return
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
        "gp": process.GenProcessor,
        "islice": process.jfislice,
        "head": process.first,
        "update": process.update,
        "tail": process.last,
        "first": process.first,
        "firstnlast": process.firstnlast,
        "headntail": process.firstnlast,
        "last": process.last,
        "null": None,
        "I": lambda arr: arr,
        "age": process.age,
        "re": re,
        "date": process.parse_value,
        "hide": process.hide,
        "unique": process.unique,
        "ipy": output.ipy,
        "csv": output.csv,
        "md": output.md,
        "browser": output.browser,
        "profile": output.profile,
        "excel": output.excel,
        "flatten": process.flatten,
        "reduce": reduce,
        "transpose": process.transpose,
        "reduce_list": process.reduce_list,
        "yield_all": process.yield_all,
        "yield_from": process.yield_all,
        "group": process.reduce_list,
        "group_by": process.group_by,
        "chain": process.reduce_list,
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
        globalscope["gp"] = process.OrderedGenProcessor

    try:
        res = eval(query, globalscope)
        for val in res:
            yield val
    except (ValueError, TypeError) as ex:
        logger.warning("Exception: %s", repr(ex))
    except SyntaxError as ex:
        logger.debug("Syntax error: %s", repr(ex))
