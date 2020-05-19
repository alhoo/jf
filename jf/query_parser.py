"""JF query parser

This module contains tools for parsing the input query when using the JF command line tool.
"""
import parser
import re
import logging

logger = logging.getLogger(__name__)


def filter_tree(node):
    """Filter interesting nodes from a parse tree"""
    if node[0] < 200:
        return [node[1]]
    subtrees = [filter_tree(subnode) for subnode in node[1:]]
    if len(subtrees) == 1:
        return subtrees[0]
    return subtrees


def flatten(tree):
    """Flatten tree"""
    logger.debug("flatten '%s'", tree)
    if maxdepth(tree) > 1:
        ret = []
        for node in tree:
            ret.extend(flatten(node))
        return ret
    return tree


def merge_not(arr, char=","):
    """Merge items until character is detected before yielding them."""
    logger.debug(arr)
    merged = ""
    for val in arr:
        if val != char:
            if merged:
                merged += " "
            merged += val
        else:
            yield merged
            merged = ""
    if merged:
        yield merged


def merge_lambdas(arr):
    """Merge jf lambdas to mappers and filters"""
    logger.debug("merge lambdas: %s", arr)
    ret = ""
    first = True
    for val, keep in arr:
        if not first:
            ret += ", "
        ret += val
        first = False
    logger.debug("ret: %s", ret)
    return ret


kwargre = re.compile(r"[^!><(=]+=[^><=]+")


def tag_keywords(val):
    """Tag keywords"""
    return val, kwargre.match(val) is None


def join_tokens(arr):
    """Join tokens if joined tokens contain the same instructions"""
    logger.debug("join_tokens '%s'", arr)
    ret = ""
    for tok in arr:
        if not ret:
            ret += tok
        elif ret[-1] not in "(){}[],.:\"'" and tok[0] not in "(){}[],.:\"'":
            ret = ret + " " + tok
        else:
            ret += tok

    return ret


def maxdepth(tree):
    """Calculate tree depth"""
    if isinstance(tree, list):
        return 1 + max([maxdepth(node) for node in tree])
    return 0


def make_param_list(part):
    """Make a parameter list from tokens"""
    logger.debug("make_param_list %s", part)
    if len(part) == 1 and isinstance(part[0], str):
        return part

    while maxdepth(part) < 4:
        part = [part]
    return list(merge_not([join_tokens(flatten(x)) for x in part]))


def parse_part(function):
    """Parse a part of pipeline definition"""
    ret = ""
    arr_set = False
    for part in function:
        logger.debug(part)
        if part[0][0] == "(":
            paramlist = [""]
            if len(part) == 3:
                paramlist = make_param_list(part[1])
            logger.debug("paramlist '%s'", paramlist)
            params = [tag_keywords(x) for x in paramlist]
            if not arr_set:
                lambda_params = merge_lambdas(params)
            else:
                lambda_params = " ".join([x[0] for x in params])
            ret += "(" + lambda_params + ")"
            arr_set = True
        elif isinstance(part[0], list):
            ret += "".join([x[0] for x in part])
        else:
            ret += "".join(part)
        logger.debug("Part: %s -> %s", part, ret)
    return ret


def parse_query(string):
    """Parse query string and convert it to a evaluatable pipeline argument"""
    logger.debug("Parsing: %s", string)
    query_tree = filter_tree(parser.expr("%s," % string).tolist())[0]
    ret = ""
    for func in query_tree:
        logger.debug("Function definition length: %d", len(func))
        if maxdepth(func) < 3:
            logger.debug("Shallow: %s", func)
            ret += func[0]
            if func[0] != ",":
                ret += "()"
            continue
        if not isinstance(func[0][0], str):
            raise SyntaxError("Weird: %s" % repr(func[0][0]))
        if func[0][0] in "{.x":
            logger.debug("Detected short syntax. Guessing.")
            func = [["map"], [["("]] + [func] + [[")"]]]
        if func[0][0] == "(":
            logger.debug("Detected short syntax. Guessing.")
            func = [["filter"], func]
        logger.debug("Parsing parts: %s", func)
        if len(func) == 2:
            part = parse_part(func)
            ret += part
        elif len(func) == 3:
            func = [[func[0][0] + "".join([x[0] for x in func[1]])], func[2]]
            logger.debug(repr(func))
            part = parse_part(func)
            ret += part
        elif len(func) > 3:
            part = parse_part(func)
            ret += part
        logger.debug("ret: %s", ret)
    return ret
