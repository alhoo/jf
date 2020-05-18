"""Pyq python json/yaml query engine"""

import sys
import json
import logging
import inspect
from datetime import datetime, timezone
from itertools import islice
from collections import deque, OrderedDict
from jf.output import result_cleaner
from jf.meta import to_struct_gen, JFTransformation

logger = logging.getLogger(__name__)


def age(datecol):
    """Try to guess the age of datestr"""
    from dateparser import parse as parsedate

    def fn(d):
        datestr = datecol.eval(d)
        logger.debug("Calculating the age of '%s'", datestr)
        try:
            ret = datetime.now() - parsedate(str(datestr))
        except TypeError:
            ret = datetime.now(timezone.utc) - parsedate(str(datestr))
        logger.debug("Age of '%s' is %s", datestr, repr(ret))
        return ret

    return fn


def parse_value(val):
    """Parse value to complex types"""
    logger.debug("Parsing date from '%s'", val)
    from dateutil import parser as dateutil

    try:
        if len(val) > 1:
            time = dateutil.parse(val)
        else:
            return val
        logger.debug("Got time '%s'", time)
        return time
    except ValueError as ex:
        logger.debug("Not a date k7j5 value: %s", val)
        logger.info(ex)
        return val


class Jfislice(JFTransformation):
    def _fn(self, arr):
        """jf wrapper for itertools.islice"""
        args = self.args
        start = None
        step = None
        stop = 1
        if isinstance(args, int):
            args = [args]
        if args:
            stop = args[0]
        if len(args) > 1:
            start = stop
            stop = args[1]
        if len(args) > 2:
            step = args[2]
        return islice(arr, start, stop, step)


class FlattenItem(JFTransformation):
    def _fn(self, it, root=""):
        """
        Make item flat
        :param it: item
        :param root: root node
        :return: flattened version of the item
        >>> FlattenItem().transform("foo")
        'foo'
        >>> FlattenItem().transform({"a": 1})
        {'a': 1}
        >>> from pprint import pprint
        >>> pprint(FlattenItem().transform({"a": 1, "b":{"c":2}}))
        {'a': 1, 'b.c': 2}
        >>> list(sorted(FlattenItem().transform({"a": 1, "b":{"c":2}}).items()))
        [('a', 1), ('b.c', 2)]
        >>> list(sorted(FlattenItem().transform({"a": 1, "b":[1,2]}).items()))
        [('a', 1), ('b.0', 1), ('b.1', 2)]
        """
        if not isinstance(it, dict):
            return it
        ret = {}
        logger.info("Flattening %s", it)
        for key, val in it.items():
            logger.info("%s: %s", key, val)
            if isinstance(val, dict):
                for k2, v2 in self.transform(val, root=key + ".").items():
                    ret[k2] = v2
            elif isinstance(val, list):
                for idx, v2 in enumerate(val):
                    dct2 = self.transform(v2, root=key + ".%d." % idx)
                    if isinstance(dct2, dict):
                        for k3, v3 in dct2.items():
                            ret[k3] = v3
                    else:
                        ret[key + ".%d" % idx] = dct2
            else:
                ret[root + key] = val
        logger.debug("Flattening %s => %s", it, ret)
        return ret


class Flatten(JFTransformation):
    def _fn(self, *args):
        """
        Flatten array
        :param args: array to flatten
        :return: array of flattened items
        >>> from pprint import pprint
        >>> pprint(list(Flatten().transform([{'a': 1, 'b':{'c': 2}}])))
        [{'a': 1, 'b.c': 2}]
        """
        logger.info("Flattening")
        arr = args[-1]
        iflat = FlattenItem()
        for it in map(result_cleaner, arr):
            yield iflat.transform(it)


class Transpose(JFTransformation):
    def _fn(self, X):
        """ Transpose input
        >>> data = [{'a': 1, 'b': 2}, {'a': 2, 'b': 3}]
        >>> arr = to_struct_gen(data)
        >>> list(sorted(map(lambda x: list(x.items()), Transpose().transform(arr)), key=lambda x: x[0][1]))
        [[(0, 1), (1, 2)], [(0, 2), (1, 3)]]
        """
        import pandas as pd

        arr = X
        data = [x.dict() for x in arr]
        df = pd.DataFrame(data)
        for it in df.to_dict(into=OrderedDict).values():
            yield it


class ReduceList(JFTransformation):
    def _fn(self, X):
        """Reduce array to a single list"""
        return [[x for x in X]]


class YieldAll(JFTransformation):
    def _fn(self, arr):
        """Yield all subitems of all item
        >>> list(YieldAll(Col().data).transform([{"data": [1,2,3]}]))
        [1, 2, 3]
        """
        for items in arr:
            for val in self.args[0](items):
                yield val


class GroupBy(JFTransformation):
    def _fn(self, arr):
        """Group items by value
        >>> arr = [{'item': '1', 'v': 2},{'item': '2', 'v': 3},{'item': '1', 'v': 3}]
        >>> x = Col()
        >>> list(sorted(map(lambda x: len(x['items']), GroupBy(x.item).transform(arr))))
        [1, 2]
        """
        ret = {}
        for item in arr:
            val = self.args[0](item)
            if val in ret:
                ret[val].append(item)
            else:
                ret[val] = [item]
        for k, v in ret.items():
            yield {"key": k, "items": v}


class Unique(JFTransformation):
    def _fn(self, X):
        """Calculate unique according to function
        >>> data = [{"a": 5, "b": 123}, {"a": 4, "b": 120}, {"a": 2, "b": 120}]
        >>> x = Col()
        >>> len(list(Unique(x.b).transform(data)))
        2
        """

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


class Hide(JFTransformation):
    def _fn(self, arr):
        """Hide elements from items"""
        elements = self.args
        for item in arr:
            yield {k: v for k, v in item.items() if k not in elements}


class Firstnlast(JFTransformation):
    def _fn(self, arr):
        """Show first and last (N) items
        >>> Firstnlast(2).transform([1,2,3,4,5])
        [[1, 2], [4, 5]]
        """
        shown = 1
        if len(self.args) == 1:
            shown = self.args[0]
        if not isinstance(shown, int):
            shown = 1
        return [list(islice(arr, 0, shown)), list(iter(deque(arr, maxlen=shown)))]


class First(JFTransformation):
    def _fn(self, arr):
        """Show first (N) items"""
        shown = 1
        if len(self.args) == 1:
            shown = self.args[0]
        if not isinstance(shown, int):
            shown = 1
        return islice(arr, 0, shown)


class Identity(JFTransformation):
    def _fn(self, X):
        return X


class Col:
    _opstrings = []

    def __setstate__(self, state):
        """
        >>> import pickle
        >>> x = Col()
        >>> col = x.v
        >>> list(map(col.eval, [{"v": 5}]))
        [5]
        >>> mb = pickle.dumps(col)
        >>> len(mb) > 0
        True
        >>> col2 = pickle.loads(mb)
        >>> list(map(col2.eval, [{"v": 10}]))
        [10]
        """
        self._opstrings = state.get("opstrings", [])
        return self

    def __getstate__(self):
        """
        The column object is pickled by only storing the opstrings.
        This is needed because the __getattr__ makes pickling hard.
        """
        state = dict(opstrings=self._opstrings)
        return state

    def __init__(self, k=None):
        if k is not None:
            self._opstrings = k

    def __call__(self, *args, **kwargs):
        return self.eval(*args, **kwargs)

    def __mul__(self, val):
        self._opstrings.append(("*", val))
        return self

    def __sub__(self, val):
        self._opstrings.append(("-", val))
        return self

    def __add__(self, val):
        self._opstrings.append(("+", val))
        return self

    def __lt__(self, val):
        self._opstrings.append(("<", val))
        return self

    def __gt__(self, val):
        self._opstrings.append((">", val))
        return self

    def __le__(self, val):
        self._opstrings.append(("<=", val))
        return self

    def __ge__(self, val):
        self._opstrings.append((">=", val))
        return self

    def __eq__(self, val):
        self._opstrings.append(("==", val))
        return self

    def __ne__(self, val):
        self._opstrings.append(("!=", val))
        return self

    def __getitem__(self, k):
        selfcopy = Col(self._opstrings + [k])
        return selfcopy

    def __getattr__(self, k):
        selfcopy = Col(self._opstrings + [k])
        return selfcopy

    def eval(self, *args, **kwargs):
        data = args[0]
        for s in self._opstrings:
            if data is None:
                return None
            if isinstance(s, str):
                s = s.replace("__JFESCAPED__", "")
                if isinstance(data, dict):
                    data = data.get(s, None)
                continue
            if isinstance(s, int):
                if isinstance(data, dict):
                    data = data.get(s, None)
                if isinstance(data, list):
                    data = data[s]
                continue
            other = s[1]
            op = s[0]
            if isinstance(other, Col):
                other = other.eval(args[0])
            if not isinstance(op, str):
                data = op(data)
                continue
            if op == "*":
                data = data * other
            if op == "+":
                data = data + other
            if op == "-":
                data = data - other
            if op == "<":
                data = data < other
            if op == ">":
                data = data > other
            if op == "==":
                data = data == other
            if op == "!=":
                data = data != other
            if op == ">=":
                data = data >= other
            if op == "<=":
                data = data <= other
            if op == "__len__":
                data = len(data)
            if op == "__str__":
                data = str(data)
        return data

    def custom(self, fn, other=None):
        self._opstrings.append((fn, other))
        return self


def fn_mod(mod):
    class FnMod:
        def __getattribute__(self, x):
            return Fn(getattr(mod, x))
    return FnMod()


def Fn(fn):
    def _fn(it):
        if isinstance(it, Col):
            return it.custom(fn)
        return fn(it)
    return _fn


TitleCase = Fn(lambda x: x.title())
Str = Fn(str)
Len = Fn(len)


def evaluate_col(col, x):
    if isinstance(col, Col):
        return col.eval(x)
    return col


class Map(JFTransformation):
    def _fn(self, X):
        """
        >>> x = Col()
        >>> list(Map(x.a).transform([{"a": 1}]))
        [1]
        """
        fn = self.args[0]
        if isinstance(fn, (tuple, list)):
            lst = fn
            fn = lambda x: [evaluate_col(col, x) for col in lst]
        if isinstance(fn, dict):
            dct = fn
            fn = lambda x: {k: evaluate_col(col, x) for k, col in dct.items()}
        if isinstance(fn, Col):
            fn = fn.eval
        ret = map(fn, X)
        if self.gen:
            return ret
        return list(ret)


class Update(JFTransformation):
    def _fn(self, X):
        """
        >>> x = Col()
        >>> list(Update({"b": x.a + 1}).transform([{"a": 1}]))
        [{'a': 1, 'b': 2}]
        """
        fn = self.args[0]
        if isinstance(fn, (tuple, list)):
            lst = fn
            fn = lambda x: [evaluate_col(col, x) for col in lst]
        if isinstance(fn, dict):
            dct = fn
            fn = lambda x: {k: evaluate_col(col, x) for k, col in dct.items()}
        if isinstance(fn, Col):
            fn = fn.eval
        for x in X:
            x.update(fn(x))
            yield x


class Filter(JFTransformation):
    def _fn(self, X):
        fn = self.args[0]
        if isinstance(fn, Col):
            fn = fn.eval
        ret = filter(fn, X)
        if self.gen:
            return ret
        return list(ret)


class Last(JFTransformation):
    def _fn(self, X):
        """Show last (N) items"""
        shown = 1
        if len(self.args) == 1:
            shown = self.args[0]
        if not isinstance(shown, int):
            shown = 1
        return iter(deque(X, maxlen=shown))
        # list(arr)[-shown:]


class Sorted(JFTransformation):
    def _fn(self, X):
        keyget = None
        if len(self.args) == 1:
            keyget = self.args[0]
        if isinstance(keyget, Col):
            keyget = keyget.eval
        ret = sorted(X, key=keyget, **self.kwargs)
        if self.gen:
            return ret
        return list(ret)


class Print(JFTransformation):
    def _fn(self, arr):
        n = 10
        if len(self.args) > 0:
            n = self.args[0]
        arr = list(arr)
        for it in islice(arr, 0, n):
            sys.stderr.write(json.dumps(it)+"\n")
        return arr


class OrderedGenProcessor:
    """Make a generator pipeline"""

    def __init__(self, igen, filters):
        """Initialize item processor
        >>> gp = OrderedGenProcessor(['a','21','3'], [JFTransformation(fn=lambda arr: map(len, arr))])
        >>> gp.add_filter(JFTransformation(fn=lambda arr: filter(lambda x: x > 1, arr)))
        >>> list(gp.process())
        [2]
        """
        self.igen = igen
        self._filters = filters

    def add_filter(self, fun):
        """Add filter to pipeline"""
        self._filters.append(fun)

    def process(self):
        """Process items"""
        pipeline = self.igen
        for fun in self._filters:
            pipeline = fun.transform(pipeline, gen=True)
        return pipeline

    def transform(self, X):
        pipeline = X
        for fun in self._filters:
            pipeline = fun.transform(pipeline, gen=True)
        return pipeline


class Pipeline:
    def __init__(self, transformations):
        self.transformations = transformations

    def transform(self, data, **kwargs):
        for t in self.transformations:
            data = t.transform(data, **kwargs)
        return data


class GenProcessor:
    """Make a generator pipeline"""

    def __init__(self, igen, filters):
        """Initialize item processor"""
        self.igen = igen
        self._filters = filters

    def add_filter(self, fun):
        """Add filter to pipeline"""
        self._filters.append(fun)

    def process(self):
        """Process items"""
        pipeline = self.igen
        for fun in self._filters:
            pipeline = fun.transform(pipeline, gen=True)
        return pipeline
