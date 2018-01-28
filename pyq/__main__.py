import sys
import json
from __init__ import *

if __name__ == "__main__":
  inq = (json.loads(d) for d in sys.stdin)
  for out in run_query(sys.argv[1], inq):
    print(json.dumps(out.__dict__))
