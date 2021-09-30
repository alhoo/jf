"""JF python json/yaml query engine

This module contains the main functions used for using the JF command line query tool
"""

import sys
import logging
from datetime import datetime, timezone
from functools import reduce
from jf.query_parser import parse_query
import jf.process as process
import jf.output as output
import jf.input as input
import jf.ml
import jf.service
import json

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
    if len(ex.args) < 2 or not isinstance(ex.args[1], (list, tuple)):
        return repr(ex.args)
    string = [c for c in ex.args[1][3]]
    start = ex.args[1][2] - ex.args[1][1]
    stop = ex.args[1][2]
    string[start] = RED + string[start]
    if stop >= len(string):
        string.append(RESET)
    else:
        string[stop] = RESET + string[stop]
    return "".join(string)


def query_convert(query):
    """Convert query for evaluation

    """
    import regex as re

    indentre = re.compile(r"\n *")
    namere = re.compile(r'([{,] *)([^{} "\[\]\',]+):')
    firstxre = re.compile(r"^(\.[a-zA-Z])")
    makexre = re.compile(r"([ (])(\.[a-zA-Z])")
    keywordunpackingre = re.compile(r"\( *\*\*x *\)")
    nowre = re.compile(r"NOW\(\)")
    logger.debug("Before conversion: %s", json.dumps(query, indent=2))
    query = indentre.sub(r" ", query)
    logger.debug("After indent removal: %s", json.dumps(query, indent=2))
    query = namere.sub(r'\1"\2":', query)
    logger.debug("After namere: %s", json.dumps(query, indent=2))
    query = firstxre.sub(r"x\1", query)
    query = makexre.sub(r"\1x\2", query)
    logger.debug("After makex: %s", json.dumps(query, indent=2))
    query = keywordunpackingre.sub("(**x.dict())", query)
    logger.debug("After kw-unpacking: %s", json.dumps(query, indent=2))
    try:
        jfkwre = re.compile(r"x\.([a-z]+)")
        query = jfkwre.sub(r"x.__JFESCAPED__\1", query)
        logger.debug("Parsing: '%s'", query)
        query = parse_query(query).rstrip(",")
    except (TypeError, SyntaxError) as ex:
        logger.warning("Syntax error in query: %s", repr(ex.args[0]))
        query = colorize(ex)
        ijfkwre = re.compile(r"x\.__JFESCAPED__([a-z]+)")
        query = ijfkwre.sub(r"x.\1", query)
        sys.stderr.write("Error in query:\n\t%s\n\n" % query)
        # raise SyntaxError
        return
    logger.debug("After query parse: %s", query)
    query = nowre.sub(r"datetime.now(timezone.utc)", query)
    logger.debug("After nowre: %s", query)
    query = "gp(data, [" + query + "]).process()"
    logger.debug("Final query '%s'", query)
    return query


def run_query(query, data, imports=None, import_from=None, ordered_dict=False):
    """Run a query against given data"""
    import regex as re

    query = query_convert(query)

    unknown = process.Col()

    globalscope = {
        "x": unknown,
        "data": data,
        "fn": process.Fn,
        "gp": process.GenProcessor,
        "islice": process.Jfislice,
        "limit": process.First,
        "head": process.First,
        "update": process.Update,
        "tail": process.Last,
        "first": process.First,
        "firstnlast": process.Firstnlast,
        "headntail": process.Firstnlast,
        "last": process.Last,
        "null": None,
        "I": process.Identity,
        "age": process.age,
        "re": re,
        "len": process.Len,
        "str": process.Str,
        "title": process.TitleCase,
        "date": process.parse_value,
        "hide": process.Hide,
        "unique": process.Unique,
        "ipy": output.ipy,
        "csv": output.csv,
        "print": process.Print,
        "md": output.md,
        "filter": jf.process.Filter,
        "browser": output.browser,
        "excel": output.excel,
        "flatten": process.Flatten,
        "parquet": output.parquet,
        "reduce": reduce,
        "map": process.Map,
        "ml": jf.ml.import_resolver,
        "service": jf.service,
        "pipeline": process.Pipeline,
        "transpose": process.Transpose,
        "reduce_list": process.ReduceList,
        "yield_all": process.YieldAll,
        "yield_from": process.YieldAll,
        "group": process.ReduceList,
        "group_by": process.GroupBy,
        "chain": process.ReduceList,
        "sorted": process.Sorted,
        "datetime": datetime,
        "timezone": timezone,
    }
    if imports:
        import importlib
        import os

        sys.path.append(os.path.dirname("."))
        if import_from:
            sys.path.append(os.path.dirname(import_from))
        globalscope.update(
            {
                imp: process.fn_mod(importlib.import_module(imp))
                for imp in imports.split(",")
            }
        )

    try:
        res = eval(query, globalscope)
        for val in res:
            yield val
    except (ValueError, TypeError) as ex:
        logger.warning("Exception: %s", repr(ex))
        raise
    except SyntaxError as ex:
        logger.debug("Syntax error: %s", repr(ex))
