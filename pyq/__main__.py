import sys
import json
import re
import argparse
import logging
import html
import yaml
from pyq import *
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
#from __init__ import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("query", help="query string for extracting wanted information", default='')
  parser.add_argument("-d", "--debug", help="print debug messages", action="store_true")
  parser.add_argument("-i", "--indent", help="output indent level", type=int, default=None)
  parser.add_argument("-y", "--yaml", help="output yaml", action='store_true')
  parser.add_argument("-j", "--json", help="output json", action='store_true')
  parser.add_argument("-s", "--sort_keys", help="sort json output values", action="store_true")
  parser.add_argument("--bw", help="remove colors", action="store_true", default=False)
  parser.add_argument("-r", "--raw", help="raw output", action="store_true", default=False)
  parser.add_argument("-a", "--ensure_ascii", help="ensure ascii only characters", action="store_true", default=False)
  parser.add_argument("--html_unescape", help="unescape html entities", action="store_true", default=False)
  args = parser.parse_args()

  if args.debug:
    logger.setLevel(logging.DEBUG)

  inq = (json.loads(d) for d in sys.stdin)
  lexertype = 'json'
  out_kw_args = {"sort_keys": args.sort_keys,
                 "indent": args.indent,
                 "cls": StructEncoder,
                 "ensure_ascii": args.ensure_ascii}
  outfmt = json.dumps
  if args.yaml and not args.json:
     outfmt = yaml.dump
     out_kw_args = {"allow_unicode": not args.ensure_ascii,
                    "indent": args.indent,
                    "default_flow_style": False}
     lexertype = 'yaml'
  lexer = get_lexer_by_name(lexertype, stripall=True)
  formatter = TerminalFormatter()
  if not sys.stdout.isatty():
    args.bw = True
  for out in run_query(args.query, inq):
    out = json.loads(json.dumps(out, cls=StructEncoder))
    ret = outfmt(out, **out_kw_args)
    if not args.raw:
      if args.html_unescape:
        ret = html.unescape(ret)
      if not args.bw:
        ret = highlight(ret, lexer, formatter).rstrip()
    else:
        ret = eval(ret)
        if type(ret) == dict:
            ret = outfmt(ret, **out_kw_args)
    print(ret)

if __name__ == "__main__":
  main()
