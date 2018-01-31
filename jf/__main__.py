"""Pyq main executable"""

import sys
import json
import argparse
import logging
import html
import fileinput
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter

from jf import run_query, StructEncoder

logger = logging.getLogger(__name__)

NORMALFORMAT = '%(levelname)s: %(message)s'
DEBUGFORMAT = '%(levelname)s %(name)s:%(lineno)d: %(message)s'

UEE = 'Got an unexpected exception'


def read_jsonl_json_or_yaml(inp, args):
    """Read json, jsonl and yaml data from file defined in args"""
    data = ''
    inf = fileinput.input(files=args.files)
    if args.yamli:
        data = "\n".join([l for l in inf])
    else:
        for val in yield_json_and_json_lines(inf):
            yield val
    if len(data) > 0:
        try:
            ind = inp(data)
            if isinstance(ind, list):
                for val in ind:
                    yield val
            else:
                yield ind
        except ValueError as ex:
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
            if char == '"':
                if state[3] < 2:
                    if item < 0:
                        item = pos
                    elif state[2] == 0:
                        yield json.loads(alldata[item:pos + 1])
                        item = -pos
                state[0] = 1 - state[0]
            if state[0] > 0:
                continue
            if char == "'":
                if state[3] < 2:
                    if item < 0:
                        item = pos
                    elif state[2] == 0:
                        yield json.loads(alldata[item:pos + 1])
                        item = -pos
                state[1] = 1 - state[1]
            if state[1] > 0:
                continue
            if char == '}':
                state[2] -= 1
                if state[2] == 0 and (not (item < 0) and alldata[item] == '{'):
                    try:
                        yield json.loads(alldata[item:pos + 1])
                        item = -pos
                    except json.JSONDecodeError as ex:
                        logger.warning("%s while yielding '%s'", UEE,
                                       alldata[item:pos + 1])
                        logger.warning("Exception %s", repr(ex))
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
                    try:
                        yield json.loads(alldata[item:pos + 1])
                        item = -pos
                    except json.JSONDecodeError as ex:
                        logger.warning("%s while yielding '%s'", UEE,
                                       alldata[item:pos + 1])
                        logger.warning("Exception %s", repr(ex))
    if item == -1 and item < pos:
        yield json.loads(alldata[0:pos + 1])


def set_loggers(debug=False):
    """Setup loggers"""
    logger_handler = logging.StreamHandler()
    liblogger = logging.getLogger('jf')
    liblogger.addHandler(logger_handler)
    if debug:
        liblogger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger_handler.setFormatter(logging.Formatter(DEBUGFORMAT))
    else:
        logger_handler.setFormatter(logging.Formatter(NORMALFORMAT))


def main(args=None):
    """Main PYQ execution function"""
    parser = argparse.ArgumentParser()
    parser.add_argument("query", default='', nargs='?',
                        help="query string for extracting wanted information")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="print debug messages")
    parser.add_argument("-i", "--indent", type=int, default=2,
                        help="pretty-printed with given indent level")
    parser.add_argument("--imports", help="import custom processing module")
    parser.add_argument("-l", "--list", action="store_true",
                        help="wrap output to a list")
    parser.add_argument("-y", "--yaml", action='store_true',
                        help="output yaml")
    parser.add_argument("--yamli", action='store_true', help="input yaml")
    parser.add_argument("-j", "--json", action='store_true',
                        help="output json")
    parser.add_argument("-s", "--sort_keys", action="store_true",
                        help="sort json output values")
    parser.add_argument("--bw", action="store_true", default=False,
                        help="remove colors")
    parser.add_argument("-r", "--raw", action="store_true", default=False,
                        help="raw output")
    parser.add_argument("-a", "--ensure_ascii", action="store_true",
                        default=False, help="ensure ascii only characters")
    parser.add_argument("--html_unescape", action="store_true", default=False,
                        help="unescape html entities")
    parser.add_argument('files', metavar='FILE', nargs='*', default="-",
                        help='files to read, if empty, stdin is used')
    args = parser.parse_args(args)

    if len(args.files) == 1 and args.files[0] == '-' and sys.stdin.isatty():
        return parser.print_help()
    if args.indent < 0:
        args.indent = None

    set_loggers(args.debug)

#    inq = (json.loads(d) for d in sys.stdin)
    inp = json.loads
    if args.yamli:
        import yaml
        inp = yaml.load

    inq = read_jsonl_json_or_yaml(inp, args)
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
    if not sys.stdout.isatty():
        args.bw = True
    try:
        retlist = []
        for out in run_query(args.query, inq, imports=args.imports):
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
                # ret = eval(ret)
                if isinstance(ret, dict):
                    ret = outfmt(ret, **out_kw_args)
            print(ret)
        if args.list:
            ret = outfmt(retlist, **out_kw_args)
            if not args.raw or args.yaml:
                if args.html_unescape:
                    ret = html.unescape(ret)
                if not args.bw:
                    ret = highlight(ret, lexer, formatter).rstrip()
            else:
                # ret = eval(ret)
                if isinstance(ret, dict):
                    ret = outfmt(ret, **out_kw_args)
            print(ret)
    except Exception as ex:
        logger.warning("%s while trying to produce results", UEE)
        logger.warning("Exception %s", repr(ex))
        raise


if __name__ == "__main__":
    main()
