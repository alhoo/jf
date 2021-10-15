from .meta import JFTransformation
from itertools import islice, chain
from queue import deque


class Flatten(JFTransformation):
    """Yield all subitems of all item

    >>> list(Flatten(lambda x: x["a"])([{"a": [1,2,3], "b": [{"c": 1}], "c": {"d": 1}}]))
    [{'a.0': 1, 'a.1': 2, 'a.2': 3, 'b.0.c': 1, 'c.d': 1}]
    """

    def _flatten(self, it, root=""):
        if not isinstance(it, dict):
            return it
        ret = {}
        for key, val in it.items():
            if isinstance(val, dict):
                for k2, v2 in self._flatten(val, root=key + ".").items():
                    ret[k2] = v2
            elif isinstance(val, list):
                for idx, v2 in enumerate(val):
                    dct2 = self._flatten(v2, root=key + ".%d." % idx)
                    if isinstance(dct2, dict):
                        for k3, v3 in dct2.items():
                            ret[k3] = v3
                    else:
                        ret[key + ".%d" % idx] = dct2
            else:
                ret[root + key] = val
        return ret

    def _fn(self, arr):
        for it in arr:
            yield self._flatten(it)


class JfDel(JFTransformation):
    """Yield all subitems of all item

    >>> list(YieldFrom(lambda x: x["a"])([{"a": [1,2,3]}]))
    [1, 2, 3]
    """

    def _fn(self, arr):
        param = self.args[0](1).split(".")
        for item in arr:
            c = item
            for p in param[:-1]:
                c = getattr(c, p)
            if param[-1] in c:
                c.__delitem__(param[-1])
            yield item


class YieldFrom(JFTransformation):
    """Yield all subitems of all item

    >>> list(YieldFrom(lambda x: x["a"])([{"a": [1,2,3]}]))
    [1, 2, 3]
    """

    def _fn(self, arr):
        for items in arr:
            for val in self.args[0](items):
                yield val


class GroupBy(JFTransformation):
    """Group items by value

    >>> list(GroupBy(lambda x: x["a"])([{"a": 1}, {"a": 1}, {"a": 2}]))
    [{1: [{'a': 1}, {'a': 1}], 2: [{'a': 2}]}]
    """

    def _fn(self, arr):
        ret = {}
        for item in arr:
            val = self.args[0](item)
            if val in ret:
                ret[val].append(item)
            else:
                ret[val] = [item]
        yield ret


class Transpose(JFTransformation):
    """Transpose input
    >>> list(Transpose(lambda x: x["a"])([{"a": 1}, {"a": 1}, {"a": 2}]))
    [{'a': [1, 1, 2]}]
    """

    def _fn(self, X):
        import pandas as pd

        df = pd.DataFrame([dict(x) for x in X])
        yield df.to_dict(orient="list")


class Unique(JFTransformation):
    """Calculate unique according to function

    >>> list(Unique(lambda x: x["a"])([{"a": 1}, {"a": 1}, {"a": 2}]))
    [{'a': 1}, {'a': 2}]
    >>> list(Unique()([{"a": 1}, {"a": 1}, {"a": 2}]))
    [{'a': 1}, {'a': 2}]
    """

    def _fn(self, X):
        def fun(x):
            return repr(x)

        if len(self.args) > 0:
            fun = self.args[0]

        seen = set()
        for it in X:
            h = hash(fun(it))
            if h in seen:
                continue
            else:
                seen.add(h)
                yield it


class Firstnlast(JFTransformation):
    """
    Show first and last (N) items
    >>> list(Firstnlast()([{"a": 1}, {"a": 1}, {"a": 2}]))
    [[{'a': 1}], [{'a': 2}]]
    >>> list(Firstnlast("1")([{"a": 1}, {"a": 1}, {"a": 2}]))
    [[{'a': 1}], [{'a': 2}]]
    """

    def _fn(self, arr):
        shown = 1
        if len(self.args) == 1:
            shown = self.args[0]
        if callable(shown):
            shown = shown(1)
        if not isinstance(shown, int):
            shown = 1
        return [list(islice(arr, 0, shown)), list(iter(deque(arr, maxlen=shown)))]


class Chain(JFTransformation):
    """
    Show only the first (N) value(s)
    >>> list(Chain()(Firstnlast(lambda x: 1)([{"a": 1}, {"a": 1}, {"a": 2}])))
    [{'a': 1}, {'a': 2}]
    """

    def _fn(self, arr):
        arr = list(arr)
        ret = chain(*arr)
        return ret


class First(JFTransformation):
    """
    Show only the first (N) value(s)
    >>> list(First(lambda x: 1)([{"a": 1}, {"a": 1}, {"a": 2}]))
    [{'a': 1}]
    >>> list(First("1")([{"a": 1}, {"a": 1}, {"a": 2}]))
    [{'a': 1}]
    """

    def _fn(self, arr):
        shown = 1
        if len(self.args) == 1:
            shown = self.args[0]
        if callable(shown):
            shown = shown(1)
        if not isinstance(shown, int):
            shown = 1
        ret = islice(arr, 0, shown)
        return ret


class Last(JFTransformation):
    """
    Show only the last (N) value(s)
    >>> list(Last(lambda x: 1)([{"a": 1}, {"a": 1}, {"a": 2}]))
    [{'a': 2}]
    >>> list(Last("1")([{"a": 1}, {"a": 1}, {"a": 2}]))
    [{'a': 2}]
    """

    def _fn(self, arr):
        shown = 1
        if len(self.args) == 1:
            shown = self.args[0]
        if callable(shown):
            shown = shown(1)
        if not isinstance(shown, int):
            shown = 1
        ret = reversed(list(First(shown)(reversed(arr))))
        return ret


class Sorted(JFTransformation):
    """
    Sort items based on the column value
    >>> list(Sorted(lambda x: x["a"])([{"a": 3}, {"a": 1}, {"a": 2}]))
    [{'a': 1}, {'a': 2}, {'a': 3}]
    """

    def _fn(self, X):
        keyget = None
        if len(self.args) == 1:
            keyget = self.args[0]
        ret = sorted(X, key=keyget, **self.kwargs)
        return ret


class Print(JFTransformation):
    """
    Print (n) values

    This prints n values to the stderr, but passes the data through without changes.

    >>> list(Print(2)([{"a": 3}, {"a": 1}, {"a": 2}]))
    [{'a': 3}, {'a': 1}, {'a': 2}]
    >>> list(Print(lambda x: 2)([{"a": 3}, {"a": 1}, {"a": 2}]))
    [{'a': 3}, {'a': 1}, {'a': 2}]
    """

    def _fn(self, arr):
        import sys
        import json

        n = 1
        if len(self.args) > 0:
            n = self.args[0]
        if callable(n):
            n = n(1)
        arr = list(arr)
        for it in islice(arr, 0, n):
            sys.stderr.write(json.dumps(it) + "\n")
        return arr


def age(datestr):
    """
    Age of a datetime string

    >>> age("1 weeks ago").days
    6
    """
    from datetime import datetime, timezone, timedelta
    from dateparser import parse as parsedate

    try:
        ret = datetime.now() - parsedate(str(datestr))
    except TypeError:
        ret = datetime.now(timezone.utc) - parsedate(str(datestr))
    return ret
