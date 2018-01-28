import sys
import json
import re
import argparse
import logging
import html
from pyq import *
#from __init__ import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[32m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("query", help="query string for extracting wanted information")
  parser.add_argument("--debug", help="print debug messages", action="store_true")
  parser.add_argument("--indent", help="output indent level", type=int, default=None)
  parser.add_argument("--sort_keys", help="sort json output values", action="store_true")
  parser.add_argument("--color", help="colorize output", action="store_true")
  parser.add_argument("--ensure_ascii", help="ensure ascii only characters", action="store_true", default=False)
  parser.add_argument("--html_unescape", help="unescape html entities", action="store_true", default=False)
  args = parser.parse_args()

  if args.debug:
    logger.setLevel(logging.DEBUG)

  colors = {
            re.compile(r'("[^,:][^"]+")([^:])'): ["bcolors.OKGREEN", ",bcolors.ENDC"],
            re.compile(r'("[^,:][^"]+")(:)'): ["bcolors.OKBLUE" + "bcolors.BOLD", ":bcolors.ENDC"],
           }

  inq = (json.loads(d) for d in sys.stdin)
  for out in run_query(args.query, inq):
    ret = json.dumps(out, sort_keys=args.sort_keys, indent=args.indent, cls=StructEncoder, ensure_ascii=args.ensure_ascii)
    if args.html_unescape:
      ret = html.unescape(ret)
    if args.color:
      for key, value in colors.items():
        ret = key.sub(value[0] + r'\1' + value[1] + r"\2", ret)
    print(ret)

if __name__ == "__main__":
  main()
