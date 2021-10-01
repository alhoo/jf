"""JF python json/yaml query engine"""

import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from itertools import islice
from collections import deque, OrderedDict
from jf.output import result_cleaner
from jf.meta import JFTransformation

logger = logging.getLogger(__name__)


def age(datecol):
    """Try to guess the age of datestr

    >>> x = Col()
    >>> isinstance(age(x.datetime)({"datetime": "2011-04-01T12:12"}), timedelta)
    True
    """
    from dateparser import parse as parsedate

    logger.info("Calculating the age of a column (%s)", datecol)

    def fn(datestr):
        logger.debug("Calculating the age of '%s'", datestr)
        try:
            ret = datetime.now() - parsedate(str(datestr))
        except TypeError:
            ret = datetime.now(timezone.utc) - parsedate(str(datestr))
        logger.debug("Age of '%s' is %s", datestr, repr(ret))
        return ret

    datecol._custom(fn)
    return datecol


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
    """jf wrapper for itertools.islice"""

    def _fn(self, arr):
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

    def _fn(self, it, root=""):
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
    """
    Flatten array

    :param args: array to flatten
    :return: array of flattened items

    >>> from pprint import pprint
    >>> pprint(list(Flatten().transform([{'a': 1, 'b':{'c': 2}}])))
    [{'a': 1, 'b.c': 2}]
    """

    def _fn(self, *args):
        logger.info("Flattening")
        arr = args[-1]
        iflat = FlattenItem()
        for it in map(result_cleaner, arr):
            yield iflat.transform(it)


class Transpose(JFTransformation):
    """ Transpose input

    >>> arr = [{'a': 1, 'b': 2}, {'a': 2, 'b': 3}]
    >>> list(sorted(map(lambda x: list(x.items()), Transpose().transform(arr)), key=lambda x: x[0][1]))
    [[(0, 1), (1, 2)], [(0, 2), (1, 3)]]
    """

    def _fn(self, X):
        import pandas as pd

        data = X
        df = pd.DataFrame(data)
        for it in df.to_dict(into=OrderedDict).values():
            yield it


class ReduceList(JFTransformation):
    def _fn(self, X):
        """Reduce array to a single list"""
        return [[x for x in X]]


class YieldAll(JFTransformation):
    """Yield all subitems of all item

    >>> list(YieldAll(Col().data).transform([{"data": [1,2,3]}]))
    [1, 2, 3]
    """

    def _fn(self, arr):
        for items in arr:
            for val in self.args[0](items):
                yield val


class GroupBy(JFTransformation):
    """Group items by value

    >>> arr = [{'item': '1', 'v': 2},{'item': '2', 'v': 3},{'item': '1', 'v': 3}]
    >>> x = Col()
    >>> list(sorted(map(lambda x: len(x), list(GroupBy(x.item).transform(arr))[0].values())))
    [1, 2]
    """

    def _fn(self, arr):
        ret = {}
        for item in arr:
            val = self.args[0](item)
            if val in ret:
                ret[val].append(item)
            else:
                ret[val] = [item]
        yield {k: v for k, v in ret.items()}


class Unique(JFTransformation):
    """Calculate unique according to function

    >>> data = [{"a": 5, "b": 123}, {"a": 4, "b": 120}, {"a": 2, "b": 120}]
    >>> x = Col()
    >>> len(list(Unique(x.b).transform(data)))
    2
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


class Hide(JFTransformation):
    """Hide elements from items

    >>> Hide("a").transform([{"a": 1, "id": 1}, {"a": 2, "id": 3}])
    [{'id': 1}, {'id': 3}]
    """

    def _fn(self, arr):
        elements = self.args
        ret = map(
            lambda item: {k: v for k, v in item.items() if k not in elements}, arr
        )
        if self.gen:
            return ret
        return list(ret)


class Firstnlast(JFTransformation):
    """
    Show first and last (N) items

    >>> Firstnlast(2).transform([1,2,3,4,5])
    [[1, 2], [4, 5]]
    """

    def _fn(self, arr):
        shown = 1
        if len(self.args) == 1:
            shown = self.args[0]
        if not isinstance(shown, int):
            shown = 1
        return [list(islice(arr, 0, shown)), list(iter(deque(arr, maxlen=shown)))]


class First(JFTransformation):
    """
    Show only the first (N) value(s)

    >>> First().transform([{"id": 99, "a": 1}, {"id": 199, "a": 2}])
    [{'id': 99, 'a': 1}]
    """

    def _fn(self, arr):
        shown = 1
        if len(self.args) == 1:
            shown = self.args[0]
        if not isinstance(shown, int):
            shown = 1
        ret = islice(arr, 0, shown)
        if self.gen:
            return ret
        return list(ret)


class Identity(JFTransformation):
    def _fn(self, X):
        return X


class Col:
    """
    Object representing a column

    This object is used to define column selection operations.
    For example if you want to select the 'id' from your data, you would do it as follows:

    >>> x = Col()
    >>> x.id({"id": 235})
    235
    """

    _opstrings = []

    def __setstate__(self, state):
        """
        >>> import pickle
        >>> x = Col()
        >>> col = x.v
        >>> list(map(col.transform, [{"v": 5}]))
        [5]
        >>> mb = pickle.dumps(col)
        >>> len(mb) > 0
        True
        >>> col2 = pickle.loads(mb)
        >>> list(map(col2.transform, [{"v": 10}]))
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
        attr = str(self._opstrings[-1])
        self._opstrings[-1] = (lambda x: getattr(x, attr)(*args, **kwargs), None)
        return self

    def __mul__(self, val):
        self._opstrings.append(("*", val))
        return self

    def __sub__(self, val):
        self._opstrings.append(("-", val))
        return self

    def __radd__(self, val):
        # self._opstrings.append(("+", val))
        self._custom(lambda x: val + x)
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

    def transform(self, *args, **kwargs):
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
                other = other.transform(args[0])
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

    def _custom(self, fn, other=None):
        """
        Apply custom function to a column

        >>> x = Col()
        >>> x.id._custom(lambda x: x > 100)({"id": 100})
        False
        >>> x.id._custom(lambda x: x > 100)({"id": 101})
        True
        """
        self._opstrings.append((fn, other))
        return self


def fn_mod(mod):
    class FnMod:
        def __getattribute__(self, x):
            # Keep classes with transform as they come
            if hasattr(getattr(mod, x), "transform"):
                return getattr(mod, x)
            # Make transformations from callables
            if callable(getattr(mod, x)):
                return Fn(getattr(mod, x))
            # Keep all the rest as they come
            return getattr(mod, x)

    return FnMod()


def Fn(fn):
    """Wrapper to convert a function to work with column selector

    This is used internally to enable nice syntax on the commandline tool

    >>> Fn(len)("123")
    3
    >>> x = Col()
    >>> Fn(len)(x.id)({"id": "123"})
    3
    """

    def _fn(it):
        if isinstance(it, Col):
            itcopy = Col([x for x in it._opstrings])
            return itcopy._custom(fn)
        return fn(it)

    return _fn


TitleCase = Fn(lambda x: x.title())
Str = Fn(str)
Len = Fn(len)


def evaluate_col(col, x):
    if isinstance(col, Col):
        return col.transform(x)
    return col


class Map(JFTransformation):
    """
    Apply simple map transformation to input data

    >>> x = Col()
    >>> list(Map(x.a).transform([{"a": 1}]))
    [1]
    """

    def _fn(self, X):
        fn = self.args[0]
        if isinstance(fn, (tuple, list)):
            lst = fn
            fn = lambda x: [evaluate_col(col, x) for col in lst]
        if isinstance(fn, dict):
            dct = fn
            fn = lambda x: {k: evaluate_col(col, x) for k, col in dct.items()}
        if isinstance(fn, Col):
            fn = fn.transform
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
            fn = fn.transform
        for x in X:
            v = fn(x)
            if isinstance(v, dict):
                x.update(**v)
            else:
                x.update(v)
            yield x


class Filter(JFTransformation):
    """
    Filter input data based on a column value

    >>> x = Col()
    >>> Filter(x.id > 100).transform([{"id": 99, "a": 1}, {"id": 199, "a": 2}])
    [{'id': 199, 'a': 2}]
    """

    def _fn(self, X):
        fn = self.args[0]
        if isinstance(fn, Col):
            fn = fn.transform
        ret = filter(fn, X)
        if self.gen:
            return ret
        return list(ret)


class Last(JFTransformation):
    """
    Show only the last (N) value(s)

    >>> Last().transform([{"id": 99, "a": 1}, {"id": 199, "a": 2}])
    [{'id': 199, 'a': 2}]
    """

    def _fn(self, X):
        """Show last (N) items"""
        shown = 1
        if len(self.args) == 1:
            shown = self.args[0]
        if not isinstance(shown, int):
            shown = 1
        ret = iter(deque(X, maxlen=shown))
        if self.gen:
            return ret
        return list(ret)
        # list(arr)[-shown:]


class Sorted(JFTransformation):
    """
    Sort items based on the column value

    >>> x = Col()
    >>> Sorted(x.a, reverse=True).transform([{"id": 99, "a": 1}, {"id": 199, "a": 2}])
    [{'id': 199, 'a': 2}, {'id': 99, 'a': 1}]
    """

    def _fn(self, X):
        keyget = None
        if len(self.args) == 1:
            keyget = self.args[0]
        if isinstance(keyget, Col):
            keyget = keyget.transform
        ret = sorted(X, key=keyget, **self.kwargs)
        if self.gen:
            return ret
        return list(ret)


class Print(JFTransformation):
    """
    Print (n) values

    This prints n values to the stderr, but passes the data through without changes.

    >>> Print().transform([1, 2, 3, 4])
    [1, 2, 3, 4]
    """

    def _fn(self, arr):
        n = 1
        if len(self.args) > 0:
            n = self.args[0]
        arr = list(arr)
        for it in islice(arr, 0, n):
            sys.stderr.write(json.dumps(it) + "\n")
        return arr


class Pipeline:
    """
    Make a pipeline from the transformations

    A pipeline in this context is a list of transformations that are applied, in order,
    to the input data stream.
    """

    def __init__(self, *transformations):
        if len(transformations) == 1 and isinstance(transformations[0], list):
            transformations = transformations[0]
        self.transformations = transformations

    def __call__(self, data, **kwargs):
        return self.transform(data, **kwargs)

    def transform(self, data, **kwargs):
        transform_one = False
        if isinstance(data, dict):
            transform_one = True
            data = [data]
        for t in self.transformations:
            data = t.transform(data, **kwargs)
        if transform_one:
            data = data[0]
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
        pipeline = Pipeline(*self._filters)
        result = pipeline.transform(self.igen, gen=True)
        return result
