import re
import sys
import json

namere = re.compile(r'([^{} "\',]+):')

class Struct:
  def __init__(self, **entries):
    for k, v in entries.items():
      if type(v) in (list, dict):
        self.__dict__[k] = to_struct(v)
      else:
        self.__dict__[k] = v
    #self.__dict__.update(entries)
  def __repr__(self):
    return self__dict
  def __getitem__(self, item):
    return self.__dict__[item]


def to_struct(v):
  if type(v) == dict:
    return Struct(**v)
  if type(v) == list:
    return [to_struct(a) for a in v]
  return v


def run_query(query, data):
  query = namere.sub(r'"\1":', query)
  return json.dumps(eval(query, {"x": to_struct(data)}))


if __name__ == "__main__":
  for d in sys.stdin:
    print(run_query(sys.argv[1], json.loads(d)))
