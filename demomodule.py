#!/usr/bin/env python3
from datetime import datetime

def timestamppipe(x, arr):
  for it in arr:
    it.update({"Pipemod": "was here at %s" % datetime.now()})
    yield it

class DuplicateRemover:
  def __init__(self, x, arr, filter=True, group=False):
    self.seen_ids = {}
    self.shown_ids = {}
    self.idfn = x
    self.filter = filter
    self.group = group
    self.arr = arr
  def show_groupped(self, mark_duplicates=None):
    ret = []
    for it in self.arr:
      iid = self.idfn(it)
      if iid in self.seen_ids:
        if iid not in self.shown_ids:
          self.shown_ids[iid] = len(ret)
          ret.append([self.seen_ids[iid]])
        if mark_duplicates:
          it = it.update(mark_duplicates(ret[self.shown_ids[iid]][0]))
        ret[self.shown_ids[iid]].append(it)
      self.seen_ids[iid] = it
    for it, v in self.seen_ids.items():
      if it not in self.shown_ids:
        ret.append([v])
    for group in ret:
      yield group
  def show(self, fn):
    for it in self.arr:
      iid = self.idfn(it)
      if iid in self.seen_ids:
        if iid not in self.shown_ids:
          yield self.seen_ids[iid]
          self.shown_ids[iid] = self.seen_ids[iid]
        yield it
      self.seen_ids[iid] = it
  def hide(self, fn=None):
    for it in self.arr:
      iid = self.idfn(it)
      if iid in self.seen_ids:
        continue
      self.seen_ids[iid] = 1
      yield it
  def process(self, fn=None):
    if self.group:
      return self.show_groupped(fn)
    elif self.filter:
      return self.hide(fn)
    else:
      return self.show(fn)
