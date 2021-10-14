import msgpack


def jf_fetch_gs(fn):
    return b'{"hello": "world"}'


def jf_serialize_msg(data):
    ret = msgpack.packb(data, use_bin_type=True)
    return ret


def jf_unserialize_msg(f):
    yield from msgpack.unpackb(f.read(), raw=False)
