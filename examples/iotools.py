def jf_fetch_psql(fn):
    import json
    import psycopg2
    from urllib import parse

    loc = parse.urlparse(fn)
    parts = loc.netloc.split("@")
    user = None
    password = None
    if len(parts) > 1:
        user, password = parts[0].split(":")
    host_ports = parts[-1].split(":")
    host = host_ports[0]
    port = 5432
    if len(host_ports) == 2:
        port = host_ports[-1]
    table = loc.fragment
    dbname = loc.path[1:]
    conn = psycopg2.connect(
        dbname=dbname, host=host, user=user, password=password, port=port
    )
    cur = conn.cursor()
    cur.execute(
        """SELECT relname FROM pg_class WHERE relkind='r'
              AND relname !~ '^(pg_|sql_)';"""
    )
    tables = [i[0] for i in cur.fetchall()]  # A list() of tables.
    try:
        cur.execute(f"SELECT * FROM {table}")
        colnames = [desc[0] for desc in cur.description]
        for line in cur.fetchall():
            yield dict(list(zip(colnames, line)))
    except:
        print(f"'{table}' not in {tables}")


def jf_fetch_gs(fn):
    return b'{"this is": "not implemented!"}'


def jf_serialize_msg(data):
    import msgpack

    ret = msgpack.packb(data, use_bin_type=True)
    return ret


def jf_unserialize_msg(f):
    import msgpack

    yield from msgpack.unpackb(f.read(), raw=False)
