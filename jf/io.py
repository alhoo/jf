"""JF io library"""
import json
import yaml
import fileinput
import logging

import sys

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import get_lexer_by_name

from jf import StructEncoder

logger = logging.getLogger(__name__)

UEE = 'Got an unexpected exception'

RED = "\033[1;31m"
BLUE = "\033[1;34m"
CYAN = "\033[1;36m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD = "\033[;1m"
REVERSE = "\033[;7m"


def colorize_json_error(text, ex):
    """Colorize syntax error"""
    string = [c for c in ex.doc]
    start = ex.pos
    stop = ex.pos + 1
    string[start] = RED+string[start]
    string[stop] = RESET+string[stop]
    return ''.join(string[max(0,start - 500):min(len(string),stop + 500)])


def print_results(data, args):
    import html
    lexertype = 'json'
    out_kw_args = {"sort_keys": args.sort_keys,
                   "indent": args.indent,
                   "cls": StructEncoder,
                   "ensure_ascii": args.ensure_ascii}
    outfmt = json.dumps
    if args.yaml and not args.json:
        import yaml
        outfmt = yaml.dump
        out_kw_args = {"allow_unicode": not args.ensure_ascii,
                       "indent": args.indent,
                       "default_flow_style": False}
        lexertype = 'yaml'
    lexer = get_lexer_by_name(lexertype, stripall=True)
    formatter = TerminalFormatter()
    if not sys.stdout.isatty() and not args.forcecolor:
        args.bw = True
    retlist = []
    for out in data:
        out = json.loads(json.dumps(out, cls=StructEncoder))
        if args.list:
            retlist.append(out)
            continue
        if lexertype == 'yaml':
            out = [out]
        ret = outfmt(out, **out_kw_args)
        if not args.raw or args.yaml:
            if args.html_unescape:
                ret = html.unescape(ret)
            if not args.bw:
                ret = highlight(ret, lexer, formatter).rstrip()
        else:
            if isinstance(ret, str):
                # Strip quotes
                ret = ret[1:-1]
        print(ret)
    if args.list:
        ret = outfmt(retlist, **out_kw_args)
        if not args.raw or args.yaml:
            if args.html_unescape:
                ret = html.unescape(ret)
            if not args.bw:
                ret = highlight(ret, lexer, formatter).rstrip()
        print(ret)


def read_jsonl_json_or_yaml(inp, args, openhook=None):
    """Read json, jsonl and yaml data from file defined in args"""
    data = ''
    inf = fileinput.input(files=args.files, openhook=openhook)
    if args.yamli:
        data = "\n".join([l for l in inf])
    else:
        for val in yield_json_and_json_lines(inf):
            try:
                yield json.loads(val)
            except json.JSONDecodeError as ex:
                # logger.warning('Error while parsing json: "%s"', ex.msg);
                logger.warning("Exception %s", repr(ex))
                jerr = colorize_json_error(data, ex)
                logger.warning("Error at code marker q4eh\ndata:\n%s", jerr);
    if len(data) > 0:
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
    alldata = ''
    item = -1
    state = [0, 0, 0, 0]
    pos = -1
    for line in inp:
        for char in line:
            pos = pos + 1
            alldata += char
            # print(char, state, char == '\\')
            if char == '\\':
                state[1] = 1
                continue
            if state[1] > 0:
                state[1] = 0
                continue
            if char == '"':
                if state[3] < 2:
                    if item < 0:
                        item = pos
                    elif state[2] == 0:
                        yield alldata[item:pos + 1]
                        item = -pos
                state[0] = 1 - state[0]
            if state[0] > 0:
                continue
            if char == '}':
                state[2] -= 1
                if state[2] == 0 and (not (item < 0) and alldata[item] == '{'):
                    yield alldata[item:pos + 1]
                    item = -pos
            elif char == '{':
                if item < 0:
                    item = pos
                state[2] += 1
            elif char == '[':
                state[3] += 1
                if state[3] > 1 and item < 0:
                    item = pos
            elif char == ']':
                state[3] -= 1
                if state[3] == 1 and (not (item < 0) and alldata[item] == '['):
                    yield json.loads(alldata[item:pos + 1])
                    item = -pos
    if item == -1 and item < pos:
        yield alldata[0:pos + 1]
