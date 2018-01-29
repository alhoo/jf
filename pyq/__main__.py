import sys
import json
import re
import argparse
import logging
import html
from pyq import *
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
#from __init__ import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("query", help="query string for extracting wanted information")
  parser.add_argument("--debug", help="print debug messages", action="store_true")
  parser.add_argument("--indent", help="output indent level", type=int, default=None)
  parser.add_argument("--sort_keys", help="sort json output values", action="store_true")
  parser.add_argument("--bw", help="remove colors", action="store_true", default=False)
  parser.add_argument("--raw", help="raw output", action="store_true", default=False)
  parser.add_argument("--ensure_ascii", help="ensure ascii only characters", action="store_true", default=False)
  parser.add_argument("--html_unescape", help="unescape html entities", action="store_true", default=False)
  args = parser.parse_args()

  if args.debug:
    logger.setLevel(logging.DEBUG)

  inq = (json.loads(d) for d in sys.stdin)
  lexer = get_lexer_by_name("json", stripall=True)
  formatter = TerminalFormatter()
  if not sys.stdout.isatty():
    args.bw = True
  for out in run_query(args.query, inq):
    ret = json.dumps(out, sort_keys=args.sort_keys, indent=args.indent, cls=StructEncoder, ensure_ascii=args.ensure_ascii)
    if not args.raw:
      if args.html_unescape:
        ret = html.unescape(ret)
      if not args.bw:
        ret = highlight(ret, lexer, formatter).rstrip()
    else:
        ret = eval(ret)
        if type(ret) == dict:
            ret = json.dumps(ret, sort_keys=args.sort_keys, indent=args.indent, cls=StructEncoder, ensure_ascii=args.ensure_ascii)
    print(ret)

if __name__ == "__main__":
  main()
