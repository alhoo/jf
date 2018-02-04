"""Pyq main executable"""

import sys
import json
import argparse
import logging
import html
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter

from jf import run_query, StructEncoder, ipy
from jf.io import read_jsonl_json_or_yaml

logger = logging.getLogger(__name__)

NORMALFORMAT = '%(levelname)s: %(message)s'
DEBUGFORMAT = '%(levelname)s %(name)s:%(lineno)d: %(message)s'

UEE = 'Got an unexpected exception'


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
    parser.add_argument("query", nargs='?', default='I',
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
    parser.add_argument("-p", "--ipy", action="store_true",
                        default=False, help="start IPython shell with data")
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
        data = run_query(args.query, inq, imports=args.imports)
        if args.ipy:
            banner = ''
            from IPython import embed
            if not sys.stdin.isatty():
                banner = '\nNotice: You are inputting data from stdin!\n' + \
                         'This might cause some trouble since jf will try ' + \
                         'to get some input from you also.\n' + \
                         'To get the full benefit of jf and IPython, ' + \
                         'consider giving the input as a file instead.\n\n' + \
                         'To prevent any unexpected behaviour, jk will ' + \
                         'load the full dataset in memory.\n' + \
                         'This might take a while...\n'
                data = list(data)
                sys.stdin = open('/dev/tty')
            ipy(banner, data)
            return
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
                elif isinstance(ret, dict):
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
