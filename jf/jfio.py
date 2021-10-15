def yield_json_and_json_lines(inp):
    """Yield json and json lines

    Split potentially huge json strings into lines or components for low memory data processing.

    Notice: Results are still json strings, so you most likely want to json.loads them.

    """
    from jf import jsonlgen

    return jsonlgen.gen(iter(inp))


class MinimalAdapter:
    """
    >>> a = MinimalAdapter()
    >>> a(iter([b"abcde", b"fghij"])).read(2)
    'ab'
    >>> a.read(2)
    'cd'
    >>> a.read(2)
    'ef'
    """

    def __init__(self):
        self._fip = None
        self._buf = None  # storage of read but unused material, maximum one line

    def __call__(self, fip):
        self._fip = fip  # store for future use
        self._buf = ""
        return self

    def read(self, size):
        if len(self._buf) >= size:
            # enough in buffer from last read, just cut it off and return
            tmp, self._buf = self._buf[:size], self._buf[size:]
            return tmp
        for line in self._fip:
            self._buf += line.decode()
            if len(self._buf) > size:
                break
        else:
            # ran out of lines, return what we have
            tmp, self._buf = self._buf, ""
            return tmp
        tmp, self._buf = self._buf[:size], self._buf[size:]
        return tmp


def get_handler(method, fntype, additionals):
    fnname = f"jf_{fntype}_{method}"
    for mod, it in additionals.items():
        if any([x == fnname for x in dir(it)]):
            return getattr(it, fnname)


def fetch_file(fn, f, additionals):
    """
    Fetch file with custom handler

    >>> from io import StringIO
    >>> s = StringIO()
    >>> class fetch_mod:
    ...     def jf_fetch_s3(m):
    ...          return '{"hello": "world"}'
    >>> fetch_file("s3://bucket/key.json", s, {"mod": fetch_mod})
    >>> s.getvalue()
    '{"hello": "world"}'
    """
    from itertools import chain

    proto = fn.split("://")[0]
    fun = get_handler(proto, "fetch", additionals)
    if fun:
        f.write(fun(fn))
        return
    raise NotImplementedError(
        f"I do not know how to fetch {proto}://.\nPlease implement {proto}(url) -> bytes and import a module with it with --import"
    )


def data_input(files=None, additionals={}, inputfmt=None):
    """
    Data input function

    >>> import tempfile
    >>> with tempfile.NamedTemporaryFile() as tmpfile:
    ...     tmpfile.write(b'[{"myconfig": "myvalue"}]') and True
    ...     tmpfile.flush()
    ...     len(list(data_input([tmpfile.name])))
    True
    1
    >>> import tempfile
    >>> with tempfile.NamedTemporaryFile(suffix=".yaml") as tmpfile:
    ...     tmpfile.write(b'[{"myconfig": "myvalue"}]') and True
    ...     tmpfile.flush()
    ...     len(list(data_input([tmpfile.name])))
    True
    1
    >>> with tempfile.NamedTemporaryFile(suffix=".csv") as tmpfile:
    ...     tmpfile.write(b"hello,world\\nno,yes\\nno,no\\n") and True
    ...     tmpfile.flush()
    ...     len(list(data_input([tmpfile.name])))
    True
    2
    >>> list(data_input(["nots3://bucket/key.json"], {}))
    Traceback (most recent call last):
    ...
    NotImplementedError: ...
    """
    import fileinput
    import json
    import sys

    pandas_ext = (
        "csv",
        "xlsx",
        "feather",
        "fwf",
        "gbq",
        "hdf",
        "html",
        "orc",
        "parquet",
        "pickle",
        "sas",
        "spss",
        "sql",
        "stata",
        "xml",
    )

    def try_json_loads(it):
        try:
            return json.loads(it)
        except Exception as ex:
            pass

    if not files:
        yield from filter(
            lambda x: x, map(try_json_loads, yield_json_and_json_lines(sys.stdin))
        )
    tmpf = None
    for fn in files:
        inputfmt = fn.split(".")[-1] if inputfmt is None else inputfmt
        inputfmt = inputfmt.split(",", 1)
        inputfmt, inputkwargs = inputfmt[0], inputfmt[1] if len(inputfmt) == 2 else ""
        inputkwargs = (
            dict([it.split("=") for it in inputkwargs.split(",")])
            if len(inputkwargs)
            else {}
        )
        if "://" in fn:
            from tempfile import NamedTemporaryFile

            tmpf = NamedTemporaryFile(suffix="." + fn.split(".")[-1], delete=False)
            fn = fetch_file(fn, tmpf, additionals)
            tmpf.close()
            fn = tmpf.name
        if inputfmt in pandas_ext:
            import pandas

            df = getattr(pandas, f"read_{inputfmt}")(fn, **inputkwargs)
            for it in df.to_dict(orient="records"):
                yield it
            continue
        if inputfmt in ("yml", "yaml"):
            import yaml

            ma = MinimalAdapter()
            with fileinput.input(
                fn, openhook=fileinput.hook_compressed, mode="rb"
            ) as f:
                ret = yaml.safe_load(ma(f))
                if isinstance(ret, list):
                    yield from ret
                else:
                    yield ret
            continue
        if not inputfmt in ("json", "jsonl"):
            fun = get_handler(fn.split(".")[-1], "unserialize", additionals)
            if fun:
                with open(fn, "rb") as f:
                    yield from fun(f)
                    continue
        with fileinput.input(fn, openhook=fileinput.hook_compressed, mode="rb") as f:
            yield from map(
                try_json_loads, yield_json_and_json_lines(map(lambda x: x.decode(), f))
            )
        if tmpf:
            import os

            os.unlink(tmpf.name)
            tmpf = None


def write_bytes(barr):
    import io
    import os
    import sys

    try:
        with os.fdopen(sys.stdout.fileno(), "wb", closefd=False) as stdout:
            stdout.write(barr)
            stdout.flush()
    except io.UnsupportedOperation:
        print("<bytes>")


def save_pandas(alldata, output, _highligh=None):
    import pandas as pd
    from io import BytesIO

    df = None
    try:
        df = pd.DataFrame([dict(it) for it in alldata])
        if output == "xlsx":
            output = "excel"
        res = BytesIO()
        try:
            getattr(df, f"to_{output}")(res)
            try:
                ret = res.getvalue().decode()
                ret = ret if not _highligh else _highligh(ret)
                print(ret)
            except:
                write_bytes(res.getvalue())
        except:
            from io import StringIO

            try:
                ress = StringIO()
                getattr(df, f"to_{output}")(ress)
                ret = ress.getvalue() if not _highligh else _highligh(ress.getvalue())
                print(ret)
            except TypeError:
                try:
                    print(getattr(df, f"to_{output}")())
                except TypeError:
                    import os
                    import tempfile

                    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
                        tmpfile.close()
                        getattr(df, f"to_{output}")(tmpfile.name)
                        with open(tmpfile.name, "rb") as f:
                            write_bytes(f.read())
                        os.unlink(tmpfile.name)
        return
    except ImportError as err:
        print(f"Failed to import required dependency for {output}")
        print(err)
    except ValueError as err:
        import sys

        sys.stderr.write("Failed to handle {}".format(alldata))
        sys.stderr.write("Failed to handle {}".format(df))
        sys.stderr.write(repr(err))


def get_supported_formats():
    """
    >>> len(get_supported_formats()) > 2
    True
    """
    import pandas as pd

    df = pd.DataFrame([{"a": 1}])
    SUPPORT_EXCLUDE = {
        "timestamp",
        "hdf",
        "sql",
        "period",
        "records",
        "dict",
        "stata",
        "gbq",
    }
    return set(
        [
            it[3:]
            for it in dir(df)
            if it.startswith("to_")
            if not it[3:] in SUPPORT_EXCLUDE
        ]
        + ["json", "jsonl", "yaml", "python", "py"]
    )


def print_results(ret, output, compact=False, raw=False, additionals={}):
    """
    Print array with various formats

    >>> data = [{"a": 1}]
    >>> print_results(data, 'help')
    - clipboard
    - csv
    ...
    >>> print_results(data, 'py', True)
    {'a': 1}
    >>> print_results(data, 'json', True)
    {"a": 1}
    >>> print_results(["hello"], 'json', True, raw=True)
    hello
    >>> print_results(data, 'json', False)
    {
      "a": 1
    }
    >>> print_results(data, 'yaml')
    - a: 1
    <BLANKLINE>
    >>> print_results(data, 'csv')
    ,a
    0,1
    <BLANKLINE>
    >>> print_results(data, 'pickle')
    <bytes>
    >>> class serialize_mod:
    ...     def jf_serialize_msg(m):
    ...          return repr(m)
    >>> print_results(data, 'msg', additionals={"mod": serialize_mod})
    <bytes>
    >>> print_results(data, 'not supported')
    Traceback (most recent call last):
    ...
    NotImplementedError: Cannot output not supported yet. Please consider making a PR!
    """
    import sys
    import json
    from pygments.lexers import get_lexer_by_name
    from pygments import highlight
    from pygments.formatters import TerminalFormatter

    if output == "yaml":
        import yaml
    if output == "help":
        import yaml

        print(yaml.dump(list(sorted(get_supported_formats()))))
        return

    class StructEncoder(json.JSONEncoder):
        """
        Try to convert everything to json

        >>> from datetime import datetime
        >>> import json
        >>> len(json.dumps(datetime.now(), cls=StructEncoder)) > 10
        True
        """

        def default(self, obj):
            try:
                return obj.__dict__
            except AttributeError:
                return obj.__str__()

    _highligh = None
    try:
        formatter = TerminalFormatter()
        lexertype = output if output != "jsonl" else "json"
        output_kwargs = {}
        if not compact:
            output_kwargs["indent"] = 2
        if sys.stdout.isatty():
            lexer = get_lexer_by_name(lexertype, stripall=True)
            _highligh = lambda line: highlight(line, lexer, formatter).rstrip()
    except:
        pass
    ret = iter(ret)
    for line in ret:
        out = line
        if output in ("python", "py"):
            line = repr(line)
        elif output == "yaml":
            line = yaml.dump([dict(line)] if isinstance(line, dict) else line)
        elif output in ("json", "jsonl"):
            line = json.dumps(
                line, ensure_ascii=False, cls=StructEncoder, **output_kwargs
            )
        else:
            alldata = [line] + list(ret)
            fun = get_handler(output, "serialize", additionals)
            if fun:
                ret = fun(alldata)
                write_bytes(ret)
                return
            try:
                return save_pandas(alldata, output, _highligh)
            except Exception as err:
                sys.stderr.write(
                    "Cant produce {}. We only know how to do {} ({})".format(
                        repr(output), get_supported_formats(), repr(err)
                    )
                )
                raise NotImplementedError(
                    f"Cannot output {output} yet. Please consider making a PR!"
                )
        if raw:
            if isinstance(out, str):
                # Strip quotes
                line = line[1:-1]
            if isinstance(out, bytes):
                sys.stdout.buffer.write(line)
            else:
                print(line)
        else:
            print(_highligh(line)) if _highligh else print(line)
