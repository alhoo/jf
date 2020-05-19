"""JF main executable"""

import sys
import json
import argparse
import logging

from jf import run_query
from jf.output import ipy, print_results
from jf.input import read_input

logger = logging.getLogger(__name__)

NORMALFORMAT = "%(levelname)s: %(message)s"
DEBUGFORMAT = "%(levelname)s %(name)s:%(lineno)d: %(message)s"

UEE = "Got an unexpected exception"


def set_loggers(debug=False):
    """Setup loggers"""
    logger_handler = logging.StreamHandler()
    liblogger = logging.getLogger("jf")
    liblogger.addHandler(logger_handler)
    if debug:
        liblogger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger_handler.setFormatter(logging.Formatter(DEBUGFORMAT))
    else:
        logger_handler.setFormatter(logging.Formatter(NORMALFORMAT))


def main(args=None):
    """Main JF execution function"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "query",
        nargs="?",
        default="I",
        help="query string for extracting wanted information",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="print debug messages"
    )
    parser.add_argument("-c", "--compact", action="store_true")
    parser.add_argument(
        "--indent", type=int, default=2, help="pretty-printed with given indent level"
    )
    parser.add_argument("--import_from", help="add path to search imports from")
    parser.add_argument("--import", help="import custom processing module")
    parser.add_argument(
        "-l", "--list", action="store_true", help="wrap output to a list"
    )
    parser.add_argument("-y", "--yaml", action="store_true", help="output yaml")
    parser.add_argument("--yamli", action="store_true", help="input yaml")
    parser.add_argument("-j", "--json", action="store_true", help="output json")
    parser.add_argument(
        "-s", "--sort_keys", action="store_true", help="sort json output values"
    )
    parser.add_argument(
        "--bw", action="store_true", default=False, help="remove colors"
    )
    parser.add_argument(
        "--ordered_dict", action="store_true", default=False, help="user ordered dict"
    )
    parser.add_argument(
        "-r", "--raw", action="store_true", default=False, help="raw output"
    )
    parser.add_argument("-f", "--cmdfile", help="read command from file")
    parser.add_argument(
        "-a",
        "--ensure_ascii",
        action="store_true",
        default=False,
        help="ensure ascii only characters",
    )
    parser.add_argument("--ipyfake", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--forcecolor", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "-p", "--ipy", action="store_true", help="start IPython shell with data"
    )
    parser.add_argument(
        "--html_unescape",
        action="store_true",
        default=False,
        help="unescape html entities",
    )
    parser.add_argument(
        "-i",
        "--input",
        metavar="FILE",
        help="files to read. Overrides files argument list",
    )
    parser.add_argument(
        "-k", "--kwargs", help="files to read. Overrides files argument list"
    )
    parser.add_argument(
        "files",
        metavar="FILE",
        nargs="*",
        default="-",
        help="files to read, if empty, stdin is used",
    )
    args = parser.parse_args(args)

    if args.input is not None:
        args.files = [args.input]

    if args.indent < 0:
        args.indent = None
    if args.compact:
        args.indent = None

    set_loggers(args.debug)

    kwargs = {}
    if args.kwargs:
        import re

        kwargsre = re.compile(r"([^:,]+)")
        kwargs = kwargsre.subn(r'"\1"', args.kwargs.replace("=", ":"))[0]
        kwargs = "{%s}" % kwargs
        kwargs = json.loads(kwargs)
    inq = read_input(args, ordered_dict=args.ordered_dict, **kwargs)
    imports = None
    if "import" in args.__dict__:
        imports = args.__dict__["import"]
    if args.cmdfile is None:
        query = args.query
    else:
        query = ", ".join(
            filter(
                lambda x: len(x) and x[0] != "#",
                open(args.cmdfile, "r").read().split("\n"),
            )
        )
        new_imports = list(
            map(
                lambda x: x.split()[1],
                filter(
                    lambda x: len(x) and x.startswith("#import "),
                    open(args.cmdfile, "r").read().split("\n"),
                ),
            )
        )
        if len(new_imports):
            if imports is None:
                imports = []
            else:
                imports = imports.split(",")
            imports = ",".join(imports + new_imports)

    if args.query == "":
        query = "I"
    data = run_query(
        query,
        inq,
        imports=imports,
        import_from=args.import_from,
        ordered_dict=args.ordered_dict,
    )
    if args.ipy or args.ipyfake:
        banner = ""
        if not sys.stdin.isatty():
            banner = (
                "\nNotice: You are inputting data from stdin!\n"
                + "This might cause some trouble since jf will try "
                + "to get some input from you also.\n"
                + "To get the full benefit of jf and IPython, "
                + "consider giving the input as a file instead.\n\n"
                + "To prevent any unexpected behaviour, jk will "
                + "load the full dataset in memory.\n"
                + "This might take a while...\n"
            )
            data = list(data)
            try:
                sys.stdin = open("/dev/tty")
            except OSError:
                pass
        ipy(banner, data, args.ipyfake)
        return
    try:
        print_results(data, args)
    except FileNotFoundError as ex:
        logger.warning("%s", ex)


if __name__ == "__main__":
    main()
