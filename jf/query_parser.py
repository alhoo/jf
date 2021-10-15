def split_query(q):
    """
    Split input query into components
    """
    pos = 0
    start = 0
    level = 0
    is_function = False
    while pos < len(q):
        if q[pos] in """([{'""":
            level += 1
        elif q[pos] in """)]}'""":
            level -= 1
            if level == 0:
                yield withquerytype(q[start : pos + 1], is_function)
                q = q[pos + 1 :]
                pos = 0
                start = 0
                is_function = False
                continue
        elif level == 0:
            if q[pos] in " ," and not is_function:
                start = start + 1
            else:
                is_function = True
        pos += 1
    if len(q):
        yield withquerytype(q[start:], is_function)


def withquerytype(query, is_function=False):
    """
    Parse query type from query component

    >>> withquerytype('{a: 5, ...}')
    ('update', '{a: 5}')
    >>> withquerytype('{a: 5}')
    ('map', '{a: 5}')
    >>> withquerytype('(.a > 5)')
    ('filter', '(.a > 5)')
    >>> withquerytype('count()', True)
    ('function', 'count()')
    >>> withquerytype('sorted(.a)', True)
    ('function', 'sorted(lambda x: (.a))')
    """
    if is_function:
        if query.startswith("unique"):
            query = query[6:]
            return "function", f"unique(lambda x: {query})"
        if query.startswith("sorted"):
            query = query[6:]
            return "function", f"sorted(lambda x: {query})"
        elif query.startswith("yield from "):
            query = query[11:]
            return "function", f"yield_from(lambda x: {query})"
        else:
            if query.startswith("x."):
                return "function", "lambda y: map(lambda x: " + query + ", y)"
            parts = query.split("(", 1)
            if len(parts) == 1:
                return "function", "lambda y: map(lambda x: " + parts[0] + ", y)"
            if len(parts[1]) < 2:
                return "function", "(".join(parts)
            ret = "function", "(lambda x: ".join(parts)
            return ret
    elif query[-1] == ")":
        return "filter", query
    elif query[-6:] == ", ...}":
        return "update", query[:-6] + "}"
    elif query[-5:] == ",...}":
        return "update", query[:-5] + "}"
    return "map", query


def query_convert(query):
    import re

    fixres = [
        [r"\|", r","],
        [r"\n *", r" "],
        [r'([{,] *)([^{} "\[\]\',]+):', r'\1"\2":'],
        [r"^(\.[a-zA-Z])", r"x\1"],
        [r"([ ({])(\.[a-zA-Z])", r"\1x\2"],
        [r'{"([^"]+)": ([^}]+ for ([^ ]+, ?)?\1(, ?[^ ]+)? in)', r"{\1: \2"],
        [r"\bdel x.([^( ]+)", r'jf_del("\1")'],
    ]
    for fixre, sub in fixres:
        query = re.sub(fixre, sub, query)
    return query


def parse_query(
    query,
    from_file=None,
    imports=[],
    import_path=None,
    debug=False,
    dosplit=True,
    inputfmt=None,
    init=[],
):
    """
    Parse user query

    >>> parse_query("{A: .b}, {c: .A, ...}, (.c>1),unique(), yield from .a")
    ('[["map", lambda x: {"A": x.b}], ["update", lambda x: {"c": x.A}], ["filter", lambda x: (x.c>1)], ["function", lambda x: unique(lambda x: ())], ["function", lambda x: yield_from(lambda x: x.a)]]', [], None, None, [])
    >>> parse_query('{timestamps: t.get(f"train/{.audio}"), ...}')
    ('[["update", lambda x: {"timestamps": t.get(f"train/{x.audio}")}]]', [], None, None, [])
    >>> parse_query('{timestamps: t.get(f"train/{.audio}"), ...}', debug=True)
    ('[["update", lambda x: {"timestamps": t.get(f"train/{x.audio}")}]]', [], None, None, [])
    >>> import tempfile
    >>> with tempfile.NamedTemporaryFile(suffix='.jf') as tmpfile:
    ...     tmpfile.write(b'#!/usr/bin/env jf\\n#import hashlib\\n{hash: hashlib.md5(.a).hexdigest(), ...}') and True
    ...     tmpfile.flush()
    ...     print(parse_query(tmpfile.name))
    True
    ('[["update", lambda x: {"hash": hashlib.md5(x.a).hexdigest()}]]', ['hashlib'], None, None, [])
    """
    if from_file or query.endswith(".jf"):
        with open(query, "r") as f:
            query = ""
            firstline = True
            for line in f:
                if firstline:
                    firstline = False
                    if line.startswith("#!"):
                        continue
                if line.startswith("#input"):
                    inputfmt = line.rstrip().split(" ", 1)[1]
                elif line.startswith("#init"):
                    init.append(line.rstrip().split(" ", 1)[1])
                elif line.startswith("#import"):
                    parts = line.rstrip().split(" ")
                    imports = list(imports) + [parts[1]]
                    if len(parts) > 3:
                        if parts[2] == "from":
                            import_path = list(import_path) + parts[3:]
                elif not line.startswith("#") and len(line) > 1:
                    query += line.rstrip()

    if not dosplit:
        return query_convert(query).replace("x.", "lambda x: x.")
    queries = list(split_query(query_convert(query)))
    queries = (
        "["
        + ", ".join([f'["{qtype}", lambda x: {query}]' for qtype, query in queries])
        + "]"
    )
    if debug:
        import sys

        sys.stderr.write(queries + "\n")
    return queries, imports, import_path, inputfmt, init
