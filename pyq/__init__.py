import regex as re
import sys
import json
import logging
from dateutil import parser as dateutil
from datetime import datetime, timezone
from itertools import islice
#from dateparser import parse as parsedate
from functools import reduce
FORMAT = '%(levelname)s %(name)s : %(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


namere = re.compile(r'([{,] *)([^{} "\',]+):')
makexre = re.compile('([ (])(\.[a-zA-Z])')
lambdare = re.compile("([a-zA-Z][^() ,]+)(\([^()]*((?2)?[^()]*)+\))")
nowre = re.compile("NOW\(\)")

def age(x):
    """Try to guess the age of x"""
    from dateparser import parse as parsedate
    logger.debug("Calculating the age of '%s'", x)
    ret = 0
    try:
        ret = datetime.now() - parsedate(str(x))
    except:
        ret = datetime.now(timezone.utc) - parsedate(str(x))
    logger.debug("Age of '%s' is %s", x, repr(ret))
    return ret

def parse_value(v):
  """Parse value to complex types"""
  try:
    if len(v) > 10:
      time = dateutil.parse(v)
    else:
      return v
    return time
  except:
    return v

class Struct:
  """Class representation of dict"""
  def __init__(self, **entries):
    self.update(entries)
  def __getitem__(self, item):
    return self.__dict__[item]
  def update(self, dct):
    for k, v in dct.items():
      if type(v) in (list, dict):
        self.__dict__[k] = to_struct(v)
      else:
        self.__dict__[k] = parse_value(v)
    return self

def to_struct(v):
  """Convert v to a class representing v"""
  if type(v) == dict:
    return Struct(**v)
  if type(v) == list:
    return [to_struct(a) for a in v]
  return v

toStruct = lambda arr: map(to_struct, arr)

class StructEncoder(json.JSONEncoder):
  """Try to convert everything to json"""
  def default(self, o):
    try:
      return o.__dict__
    except:
      return o.__str__()

def pipelogger(arr):
  for it in arr:
    logger.debug("'%s' goes through the pipeline", it)
    yield it

def pyqislice(*args):
    arr = args[-1]
    args = args[0](0)
    start = None
    step = None
    stop = 1 
    if type(args) == int:
        args = [args]
    if len(args) > 0:
        stop = args[0]
    if type(stop) != int:
        stop = 1
    if len(args) > 1:
        start = stop
        stop = args[1]
    if type(stop) != int:
        stop = 1
    if len(args) > 2:
        step = args[2]
    if type(step) != int:
        step = 1
    print(start, stop, step)
    return islice(arr, start, stop, step)
    
    #lambda *x, arr: islice(arr, *x),
def first(*args):
    arr = args[-1]
    if len(args) == 2:
        N = args[0](arr)
    if type(N) != int:
        N = 1
    return islice(arr, 0, N)

def last(*args):
    arr = args[-1]
    if len(args) == 2:
        N = args[0](arr)
    if type(N) != int:
        N = 1
    return list(arr)[-N:]

class genProcessor:
  """Make a generator pipeline"""
  def __init__(self, igen, filters=[]):
    self.igen = igen
    self._filters = filters
  def process(self):
    pipeline = self.igen
    pipeline = pipelogger(pipeline)
    for f in self._filters:
      pipeline = f(toStruct(pipeline))
    return pipeline

def run_query(query, data, sort_keys=False):
  """Run a query against given data"""
  logger.debug(query)
  query = namere.sub(r'\1"\2":', query)
  logger.debug(query)
  query = makexre.sub(r'\1x\2', query)
  logger.debug(query)
  query = lambdare.sub(r'lambda arr: \1(lambda x, *rest: \2, arr)', query)
  logger.debug(query)
  query = nowre.sub(r'datetime.now(timezone.utc)', query)
  logger.debug(query)
  query = "gp(data, [" + query + "]).process()" #Make it a list
  logger.debug("Final query '%s'", query)
  globalscope = {
      "data": data,
      "gp": genProcessor,
      "islice": pyqislice,
      "first": first,
      "last": last,
      "age": age,
      "reduce": reduce,
      "sorted": lambda x, arr: sorted(arr, key=x),
      "datetime": datetime,
      "timezone": timezone}
  res = eval(query, globalscope)
  try:
    for it in res:
      yield it
  except TypeError as ex:
    yield res
  except Exception as ex:
    logger.warning("Got an unexpected exception while yielding results")
    logger.warning("Exception: %s", ex)


#if __name__ == "__main__":
#  inq = (json.loads(d) for d in sys.stdin)
#  for out in run_query(sys.argv[1], inq):
#    print(json.dumps(out, cls=StructEncoder))
