"""JF python json/yaml query engine"""

import sys
import json
import logging
from itertools import islice, chain
from collections import deque, OrderedDict

from jf.meta import StructEncoder, JFTransformation

from pygments.lexers import get_lexer_by_name
from pygments import highlight
from pygments.formatters import TerminalFormatter


logger = logging.getLogger(__name__)


def print_results(data, args):
    """Print results"""
    import html

    lexertype = "json"
    out_kw_args = {
        "sort_keys": args.sort_keys,
        "indent": args.indent,
        "cls": StructEncoder,
        "ensure_ascii": args.ensure_ascii,
    }
    outfmt = json.dumps
    if args.yaml and not args.json:
        from ruamel import yaml

        yaml.RoundTripDumper.add_representer(
            OrderedDict, yaml.RoundTripRepresenter.represent_dict
        )

        outfmt = yaml.dump

        out_kw_args = {
            "allow_unicode": not args.ensure_ascii,
            "indent": args.indent,
            "default_flow_style": False,
            "Dumper": yaml.RoundTripDumper,
        }
        lexertype = "yaml"
    lexer = get_lexer_by_name(lexertype, stripall=True)
    formatter = TerminalFormatter()
    if not sys.stdout.isatty() and not args.forcecolor:
        args.bw = True
    retlist = []
    try:
        for out in data:
            if args.ordered_dict:
                if isinstance(out, list):
                    out = json.loads(
                        json.dumps(out, cls=StructEncoder),
                        object_pairs_hook=OrderedDict,
                    )
                elif not isinstance(out, str):
                    out = json.loads(
                        json.dumps(out, cls=StructEncoder),
                        object_pairs_hook=OrderedDict,
                    )
                elif args.raw:
                    if isinstance(out, bytes):
                        sys.stdout.write(out)
                    else:
                        print(out)
                    continue
            elif not args.raw:
                out = json.loads(json.dumps(out, cls=StructEncoder))
            if args.list:
                retlist.append(out)
                continue
            if lexertype == "yaml":
                out = [out]
            ret = outfmt(out, **out_kw_args)
            if not args.raw or args.yaml:
                if args.html_unescape:
                    ret = html.unescape(ret)
                if not args.bw:
                    ret = highlight(ret, lexer, formatter).rstrip()
            else:
                if isinstance(out, str):
                    # Strip quotes
                    ret = ret[1:-1]
            if isinstance(out, bytes):
                sys.stdout.buffer.write(out)
            else:
                print(ret)
        if args.list:
            ret = outfmt(retlist, **out_kw_args)
            if not args.raw or args.yaml:
                if args.html_unescape:
                    ret = html.unescape(ret)
                if not args.bw:
                    ret = highlight(ret, lexer, formatter).rstrip()
            if isinstance(ret, bytes):
                sys.stdout.write(ret)
            else:
                print(ret)
    except BrokenPipeError:
        return


def peek(data, count=100):
    """Slice and memoize data head"""
    head = list(islice(data, 0, count))
    if isinstance(data, (list, tuple, dict)):
        data = islice(data, count, None)
    return head, chain(head, data)


def result_cleaner(val):
    """Cleanup the result

    >>> result_cleaner({'a': 1})
    {'a': 1}
    """
    if isinstance(val, OrderedDict):
        return json.loads(
            json.dumps(val, cls=StructEncoder), object_pairs_hook=OrderedDict
        )
    return json.loads(json.dumps(val, cls=StructEncoder))


class pandasWriter(JFTransformation):
    """General pandas writer"""

    def _fn(self, arr):
        import pandas as pd

        logger.info(
            "Writing excel with args: %s and kwargs: %s", self.args, self.kwargs
        )
        df = pd.DataFrame(list(map(result_cleaner, arr)))
        if len(self.args) > 0:
            fn = self.args[0]
            getattr(df, self.writefn)(fn, *self.args[1:], **self.kwargs)
            yield f"data written to {fn}"
        else:
            import tempfile

            f = tempfile.NamedTemporaryFile(delete=False)
            f.close()
            fn = f.name
            getattr(df, self.writefn)(fn, *self.args[1:], **self.kwargs)
            with open(f.name, "rb") as f:
                content = f.read()
            yield content


class parquet(pandasWriter):
    """Convert input to parquet

    >>> list(parquet("/tmp/test.parq").transform([{'a': 1}, {'a': 3}]))
    ['data written to /tmp/test.parq']
    """

    def __init__(self, *args, **kwargs):
        super(parquet, self).__init__(*args, **kwargs)

        self.writefn = "to_parquet"
        self.kwargs.update({"engine": "pyarrow"})
        # self.kwargs.update({"compression": "GZIP"})


class excel(pandasWriter):
    """Convert input to excel

    >>> list(excel("/tmp/test.xlsx").transform([{'a': 1}, {'a': 3}]))
    ['data written to /tmp/test.xlsx']
    """

    def __init__(self, *args, **kwargs):
        super(excel, self).__init__(*args, **kwargs)
        self.writefn = "to_excel"


class browser(JFTransformation):
    """ Send output to browser
    """

    def _fn(self, arr):
        import webbrowser
        import tempfile
        import time

        with tempfile.NamedTemporaryFile("w") as f:
            for line in arr:
                f.write(line)
            webbrowser.open(f.name, **self.kwargs)
            time.sleep(1)  # Hack to give the browser some time to start


class md(JFTransformation):
    """ Convert dict to markdown

    >>> md().transform([OrderedDict([("a", 1), ("b", 2)]),OrderedDict([("a", 2), ("b", 3)])])
    a  |  b
    ---|---
    1  |  2
    2  |  3
    """

    def _fn(self, arr):
        from csvtomd import md_table
        from math import isnan

        if len(self.args) > 1:
            args = [open(self.args[0], "w")]
        else:
            args = []
        table = []
        first = True
        for row in map(result_cleaner, arr):
            logger.info("Writing row %s", row)
            if first:
                table.append([str(v) if v else "" for v in row.keys()])
                first = False
            table.append(
                [
                    str(v) if isinstance(v, str) or not isnan(v) else ""
                    for v in row.values()
                ]
            )
        if len(args):
            args[0].write(md_table(table, **self.kwargs) + "\n")
        else:
            print(md_table(table, **self.kwargs))


class csv(JFTransformation):
    """ Convert dict to csv

    >>> csv(lineterminator="\\n").transform([OrderedDict([("a", 1), ("b", 2)]),OrderedDict([("a", 2), ("b", 3)])])
    a,b
    1,2
    2,3
    """

    def _fn(self, arr):
        from csv import writer as cvs_writer

        if len(self.args) > 1:
            args = [open(self.args[0], "w")]
        else:
            args = [sys.stdout]
        r = cvs_writer(*args, **self.kwargs)
        first = True
        for row in map(result_cleaner, arr):
            logger.info("Writing row %s", row)
            if first:
                r.writerow(row.keys())
                first = False
            r.writerow(row.values())


class ipy(JFTransformation):
    """Start ipython with data-variable"""

    def _fn(self, data):
        from IPython import embed

        banner = self.args[0]
        fakerun = False
        if "fakerun" in self.kwargs:
            fakerun = True
            del self.kwargs["fakerun"]
        if not isinstance(banner, str):
            banner = ""
        banner += "\nJf instance is now dropping into IPython\n"
        banner += "Your filtered dataset is loaded in a iterable variable "
        banner += 'named "data"\n\ndata sample:\n'
        head, data = peek(map(result_cleaner, data), 1)
        if head:
            banner += json.dumps(head[0], indent=2, sort_keys=True)
        banner += "\n\n"
        if not fakerun:
            embed(banner1=banner)
