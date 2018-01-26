import sys
import json
from __init__ import *

if __name__ == "__main__":
  for d in sys.stdin:
    print(run_query(sys.argv[1], json.loads(d)))
