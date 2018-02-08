"""Pyq main executable"""

import sys
import json
import argparse
import logging

from jf import run_query, ipy
from jf.io import read_jsonl_json_or_yaml, print_results

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
    parser.add_argument('--ipyfake', action="store_true",
                        help=argparse.SUPPRESS)
    parser.add_argument('--forcecolor', action="store_true",
                        help=argparse.SUPPRESS)
    parser.add_argument("-p", "--ipy", action="store_true",
                        help="start IPython shell with data")
    parser.add_argument("--html_unescape", action="store_true", default=False,
                        help="unescape html entities")
    parser.add_argument('--input', metavar='FILE',
                        help='files to read. Overrides files argument list')
    parser.add_argument('files', metavar='FILE', nargs='*', default="-",
                        help='files to read, if empty, stdin is used')
    args = parser.parse_args(args)

    if args.input != None:
        args.files = [args.input]

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
    data = run_query(args.query, inq, imports=args.imports)
    if args.ipy or args.ipyfake:
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
        ipy(banner, data, args.ipyfake)
        return
    print_results(data, args)


if __name__ == "__main__":
    main()
