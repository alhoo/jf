_funcs = None


class DotAccessibleNone:
    __dict__ = None

    def __getattr__(self, k):
        return DotAccessibleNone()


class DotAccessible(dict):
    """
    Dot accessible version of a dict. For syntactic sugar.

    >>> it = DotAccessible({"a": 5})
    >>> it.a
    5
    >>> it.b = 6
    >>> it
    {'a': 5, 'b': 6}
    >>> del it.b
    >>> isinstance(it.b, DotAccessibleNone)
    True
    >>> it
    {'a': 5}
    >>> DotAccessible({"a": 5}, b=1)
    {'a': 5, 'b': 1}
    """

    def __init__(self, *args, **kwargs):
        super(DotAccessible, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    self[k] = dotaccessible(v)

        if kwargs:
            for k, v in kwargs.items():
                self[k] = dotaccessible(v)

    def __getattr__(self, k):
        return dotaccessible(
            self.get(k) if not k.startswith("__") else super().__getattr__(k)
        )

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(DotAccessible, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(DotAccessible, self).__delitem__(key)
        del self.__dict__[key]


def undotaccessible(it):
    if isinstance(it, dict):
        return {k: undotaccessible(v) for k, v in dict.items(it)}
    if isinstance(it, list):
        return [undotaccessible(v) for v in it]
    return it


def dotaccessible(it):
    if it is None:
        return DotAccessibleNone()
    if isinstance(it, dict):
        return DotAccessible(it)
    return it


def worker_init(funcs):
    """
    initializer for the worker in multiprocessing
    """
    global _funcs
    _funcs = funcs


class JFREMOVED:
    pass


def worker(x):
    """
    worker for multiprocessing
    >>> worker_init([["map", lambda x: x],
    ...              ["update", lambda x: x],
    ...              ["function", lambda x: lambda y: y],
    ...              ["filter", lambda x: x]])
    >>> worker({"a": 1})
    {'a': 1}
    """
    for op, _func in _funcs:
        if op == "map":
            x = _func(dotaccessible(x))
        elif op == "update":
            x.update(_func(dotaccessible(x)))
        elif op == "function":
            x = _func(dotaccessible(x))(dotaccessible(x))
        elif op == "filter":
            test = _func(dotaccessible(x))
            if not test:
                return JFREMOVED
    return x


def dict_updater(_f):
    def _update_dict(x):
        return dict(x, **_f(x))

    return _update_dict


def mymap(fs, arr, processes=1):
    """My mapping function

    Apply functions in fs to items in arr. Also supports multiprocessing.

    """
    if processes > 1:
        from multiprocessing import Pool

        with Pool(
            processes,
            initializer=worker_init,
            initargs=([(op, f) for op, f in fs if op != "function"],),
        ) as pool:
            ret = pool.imap(worker, arr, chunksize=16)
            for op, f in fs:
                if op == "function":
                    ret = f(ret)(map(dotaccessible, ret))
            yield from filter(lambda x: x != JFREMOVED, ret)
    else:
        for op, _f in fs:
            if op == "map":
                arr = map(_f, map(dotaccessible, arr))
            elif op == "update":
                arr = map(dict_updater(_f), map(dotaccessible, arr))
            elif op == "function":
                arr = _f(1)(map(dotaccessible, arr))
            elif op == "filter":
                arr = filter(_f, map(dotaccessible, arr))
        yield from arr


def camel_to_snake(name):
    import re

    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return name


def HttpServe(fs, listen, processes):
    import json
    from flask import Flask, request, Response
    from time import sleep

    app = Flask(__name__)
    data = []
    results = []

    def format_sse(ev):
        try:
            data_json = json.dumps(ev)
            return f'data: {data_json}\n\n'
        except TypeError:
            print(f"Failed to json encode {ev}")

    @app.route("/jf", methods=["GET"])
    def ui():
        with open("index.html") as f:
            return f.read()

    @app.route("/v0/analytics-events-definitions", methods=["GET"])
    def mf_get_analytics_definitions():
        return '{"blacklist": ["dummy:blocked"], "enable_client_analytics": true, "enable_server_analytics": true, "build_version": "missing"}'

    @app.route('/sse', methods=['GET'])
    def sse():
        def evstream():
            pos = len(results)
            while True:
                while len(results) > pos:
                    it = format_sse(results[pos])
                    if it:
                        yield it
                    pos += 1
                if len(results) < pos:
                    pos = len(results)
                sleep(.2)
        return Response(evstream(), mimetype='text/event-stream')

    @app.route("/I", methods=["GET"])
    def get_data():
        return json.dumps(data)

    @app.route("/T", methods=["GET"])
    def get_results():
        try:
            data_json = json.dumps(results)
            return data_json
        except TypeError:
            print(f"Failed to json encode {results}")

    @app.route("/empty", methods=["POST"])
    def clear_results():
        rlen = len(results)
        while rlen > 0:
            del results[rlen - 1]
            rlen = len(results)
        return "ok"

    @app.route("/", methods=["POST", "PUT"])
    def index():
        data.append(request.json)
        arr = [request.json]
        for op, _f in fs:
            if op == "map":
                arr = map(_f, map(dotaccessible, arr))
            elif op == "update":
                arr = map(dict_updater(_f), map(dotaccessible, arr))
            elif op == "function":
                arr = _f(1)(map(dotaccessible, arr))
            elif op == "filter":
                arr = filter(_f, map(dotaccessible, arr))
        ret = undotaccessible(next(arr))
        results.append(ret)
        return json.dumps(ret)

    app.run(host="0.0.0.0", port=listen)


def run_query(query, data, additionals={}, from_file=False, processes=1, listen=False):
    """
    Run query. This function will utilize global imports if used as a library:

    >>> import hashlib
    >>> list(run_query('.a', [{"a": "521"}, {"a": "643"}]))
    ['521', '643']
    """
    from .query_parser import parse_query
    from . import extra_functions

    # query
    queries, imports, import_path, _, _ = parse_query(query, from_file, [], [], False)

    name_alternatives = {
        "first": ["head"],
        "last": ["tail"],
        "firstnlast": ["headntail"],
    }

    # environment
    world = dict(
        {"data": data, "mymap": mymap},
        **{
            camel_to_snake(k): getattr(extra_functions, orig_k)
            for orig_k in dir(extra_functions)
            if orig_k[0] != "_"
            for k in name_alternatives.get(camel_to_snake(orig_k), []) + [orig_k]
        },
    )
    if additionals:
        world.update(additionals)
    else:
        import inspect

        def superglobals():
            _globals = dict(
                inspect.getmembers(inspect.stack()[len(inspect.stack()) - 1][0])
            )["f_globals"]
            return _globals

        world.update({k: v for k, v in superglobals().items() if "_" != k[0]})

    for init in additionals.get("JF_init_codes", []):
        eval(init, world)

    if listen:
        world.update({"HttpServe": HttpServe})
        return eval(f"HttpServe({queries}, {listen}, {processes})", world)
    else:
        # process
        return eval(f"mymap({queries}, data, {processes})", world)
