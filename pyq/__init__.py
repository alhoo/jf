import re
import sys
import json
import logging
from functools import reduce
logger = logging.getLogger(__name__)
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


namere = re.compile(r'([{,] *)([^{} "\',]+):')
lambdare = re.compile("([a-zA-Z][^ ,]+)\(([^)]+)\)")

class Struct:
  def __init__(self, **entries):
    for k, v in entries.items():
      if type(v) in (list, dict):
        self.__dict__[k] = to_struct(v)
      else:
        self.__dict__[k] = v
  def __getitem__(self, item):
    return self.__dict__[item]

def to_struct(v):
  if type(v) == dict:
    return Struct(**v)
  if type(v) == list:
    return [to_struct(a) for a in v]
  return v

toStruct = lambda arr: map(to_struct, arr)

class genProcessor:
  def __init__(self, igen, filters=[]):
    self.igen = igen
    self._filters = filters
  def process(self):
    pipeline = self.igen
    for f in self._filters:
      pipeline = f(toStruct(pipeline))
    return pipeline

def run_query(query, data, sort_keys=False):
  query = namere.sub(r'\1"\2":', query)
  query = lambdare.sub(r'lambda arr: \1(lambda x: \2, arr)', query)
  query = "gp(x, [" + query + "]).process()" #Make it a list
  logger.debug(query)
  for it in eval(query, {"x": data, "gp": genProcessor, "reduce": reduce}):
    yield it


if __name__ == "__main__":
  inq = (json.loads(d) for d in sys.stdin)
  for out in run_query(sys.argv[1], inq):
    print(out.__dict__)
