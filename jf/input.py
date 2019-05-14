"""JF io library"""
import fileinput
import logging

from collections import OrderedDict

import json
import yaml

from lxml import etree

from jf import jsonlgen   # cpython from jsonlgen.cc

logger = logging.getLogger(__name__)

UEE = 'Got an unexpected exception'

RED = "\033[1;31m"
BLUE = "\033[1;34m"
CYAN = "\033[1;36m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD = "\033[;1m"
REVERSE = "\033[;7m"


def format_xml(parent):
    """
    Recursive operation which returns a tree formated
    as dicts and lists.
    Decision to add a list is to find the 'List' word
    in the actual parent tag.
    >>> tree = etree.fromstring('<doc><a>1</a></doc>')
    >>> format_xml(tree)
    {'a': '1'}
    """
    ret = {}
    try:
        if parent.items():
            ret.update(dict(parent.items()))
        if parent.text:
            ret['__content__'] = parent.text
        if 'List' in parent.tag:
            ret['__list__'] = []
            for element in parent:
                ret['__list__'].append(format_xml(element))
        else:
            for element in parent:
                if element.tag not in ret:
                    ret[element.tag] = []
                ret[element.tag].append(format_xml(element))
        if len(ret) == 1 and '__content__' in ret:
            return ret['__content__']
        elif '__content__' in ret:
            del ret['__content__']
        for key in list(ret.keys()):
            if not isinstance(key, str):
                del ret[key]
            elif len(ret[key]) == 1:
                ret[key] = ret[key][0]
    except Exception as ex:
        logger.info("Error while decoding xml %s", ex)
    return ret


def colorize_json_error(ex):
    """Colorize syntax error"""
    string = [c for c in ex.doc]
    start = ex.pos
    stop = ex.pos + 1
    string[start] = RED+string[start]
    string[stop] = RESET+string[stop]
    return ''.join(string[max(0, start - 500):min(len(string), stop + 500)])


def import_error():
        logger.warning("Install pandas and xlrd to read csv and excel")
        logger.warning("pip install pandas")
        logger.warning("pip install xlrd")


def read_input(args, openhook=fileinput.hook_compressed, ordered_dict=False,
               **kwargs):
    """Read json, jsonl and yaml data from file defined in args"""
    try:
        # FIXME these only output from the first line
        if args.files[0].endswith("xml"):
            tree = etree.parse(args.files[0])
            root = tree.getroot()
            xmldict = format_xml(root)
            logger.info("Got dict from xml %s", xmldict)
            yield xmldict
            return
        elif args.files[0].endswith("xlsx"):
            import xlrd
            import pandas
            for val in pandas.read_excel(args.files[0]).to_dict("records", into=OrderedDict):
                yield val
            return
        elif args.files[0].endswith("csv"):
            import pandas
            if ordered_dict:
                for val in pandas.read_csv(args.files[0], **kwargs).to_dict("records", into=OrderedDict):
                    yield val
            else:
                for val in pandas.read_csv(args.files[0], **kwargs).to_dict("records"):
                    yield val
            return
    except ImportError:
        return import_error()

    data = ''
    inp = json.loads
    inf = (x.decode('UTF-8') for x in
           fileinput.input(files=args.files, openhook=openhook, mode='rb'))

    def generic_constructor(loader, tag, node):
        classname = node.__class__.__name__
        if classname == 'SequenceNode':
            return loader.construct_sequence(node)
        elif classname == 'MappingNode':
            return loader.construct_mapping(node)
        else:
            return loader.construct_scalar(node)

    yaml.add_multi_constructor('', generic_constructor)

    if args.yamli or args.files[0].endswith("yaml") or args.files[0].endswith("yml"):

        inp = yaml.load
        data = "\n".join([l for l in inf])
    else:
        for val in yield_json_and_json_lines(inf):
            try:
                obj = json.loads(val, object_pairs_hook=OrderedDict)
                yield obj
            except json.JSONDecodeError as ex:
                logger.warning("Exception %s", repr(ex))
                jerr = colorize_json_error(ex)
                logger.warning("Error at code marker q4eh\ndata:\n%s", jerr)
    if data:
        try:
            ind = inp(data)
            if isinstance(ind, list):
                for val in ind:
                    yield val
            else:
                yield ind
        except yaml.parser.ParserError as ex:
            logger.warning("%s while producing input data", UEE)
            logger.warning("Exception %s", repr(ex))


def yield_json_and_json_lines(inp):
    """Yield  json and json lines"""
    return jsonlgen.gen(iter(inp))
