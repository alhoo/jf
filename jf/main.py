from .query_parser import parse_query
from .process import run_query, dotaccessible
from .jfio import data_input, print_results


def jf(
    processes,
    query_and_files,
    imports,
    import_path,
    from_file,
    compact,
    inputfmt,
    output,
    debug,
    raw,
    init,
):
    """Main of the machine

    >>> import tempfile
    >>> import json
    >>> def run_with_data(data, jffn):
    ...     with tempfile.NamedTemporaryFile(suffix='.json') as tmpfile:
    ...         tmpfile.write(json.dumps(data).encode()) and True
    ...         tmpfile.flush()
    ...         jffn(tmpfile.name)
    >>> def jffn(query, *args):
    ...     def _fn(fname):
    ...         ret1 = jf(1, [query, fname], *args)
    ...         ret2 = jf(2, [query, fname], *args)
    ...         assert ret1 == ret2
    ...     return _fn
    >>> run_with_data([{"a": "myvalue"}], jffn(".a", [], [], False, True, None, 'json', False, False, []))
    "myvalue"
    "myvalue"
    >>> run_with_data([{"a": "myvalue"}], jffn("{b: .a}", [], [], False, True, None, 'json', False, False, []))
    {"b": "myvalue"}
    {"b": "myvalue"}
    >>> run_with_data([{"a": 1}, {"a": 2}], jffn("(.a > 1)", [], [], False, True, None, 'json', False, False, []))
    {"a": 2}
    {"a": 2}
    >>> run_with_data([{"a": "myvalue"}], jffn("{hash: hashlib.md5(.a.encode()).hexdigest(), ...}", ["hashlib"], [], False, True, None, 'json', False, False, []))
    {"a": "myvalue", "hash": "d724a7135ce7d2593c25fc5212d4125a"}
    {"a": "myvalue", "hash": "d724a7135ce7d2593c25fc5212d4125a"}
    >>> run_with_data([{"a": "myvalue"}], jffn("{hash: hashlib.md5(.a.encode()).hexdigest(),...}", ["hashlib", "iotools"], ["examples"], False, True, None, 'msg', False, False, []))
    <bytes>
    <bytes>
    >>> run_with_data([{"a": "myvalue"}], jffn("{hash: hashlib.md5(.a.encode()).hexdigest(), c: C, ...}", ["hashlib"], [], False, True, None, 'json', False, False, ["C=5"]))
    {"a": "myvalue", "hash": "d724a7135ce7d2593c25fc5212d4125a", "c": 5}
    {"a": "myvalue", "hash": "d724a7135ce7d2593c25fc5212d4125a", "c": 5}
    """
    import os

    query = "x"
    files = []
    if len(query_and_files) > 0:
        query = query_and_files[0]
    if len(query_and_files) > 1:
        files = query_and_files[1:]

    # input query
    queries, imports, import_path, inputfmt, init = parse_query(
        query,
        from_file,
        imports,
        import_path,
        debug,
        inputfmt=inputfmt,
        init=list(init),
    )

    # environment
    additionals = list(filter(lambda x: is_datafile(x), imports))
    imports = list(filter(lambda x: not is_datafile(x), imports))
    additionals = {
        name(filename): list(map(dotaccessible, data_input([filepath(filename)])))
        for filename in additionals
    }
    additionals = {k: v[0] if len(v) == 1 else v for k, v in additionals.items()}
    additionals["env"] = dotaccessible({k: v for k, v in os.environ.items()})
    if imports:
        import importlib
        import sys
        import os

        sys.path.append(os.path.dirname("."))
        for path in import_path:
            sys.path.append(path)
        additionals.update(
            dict(
                [[name(imp), importlib.import_module(filepath(imp))] for imp in imports]
            )
        )
    additionals["JF_init_codes"] = [parse_query(i, dosplit=False) for i in init]

    # input data
    data = data_input(files, additionals, inputfmt)

    # processing
    ret = run_query(query, data, additionals, from_file, processes)

    # output
    print_results(ret, output, compact, raw, additionals)


def filepath(x):
    return x.split("=")[-1]


def name(x):
    return x.split("=")[0].split(".")[0]


def is_datafile(x):
    return x.endswith(".json")
