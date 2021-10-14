from ctypes import *
from ctypes.util import find_library
import subprocess

libsox = cdll.LoadLibrary(find_library("sox"))


class SignalInfo(Structure):
    """
    sox_signalinfo_t as per source (1)


    (1) https://sourceforge.net/p/sox/code/ci/master/tree/src/sox.h#l1349
    """

    _fields_ = [
        ("rate", c_double),
        ("channels", c_ubyte),
        ("precision", c_ubyte),
        ("length", c_ulonglong),
        ("mult", c_void_p),
    ]


class EncodingInfo(Structure):
    """
    sox_encodinginfo_t as per source (1)


    (1) https://sourceforge.net/p/sox/code/ci/master/tree/src/sox.h#l1371
    """

    _fields_ = [
        ("encoding", c_int),
        ("bits_per_sample", c_uint),
        ("reverse_bytes", c_int),
        ("reverse_nibbles", c_int),
        ("reverse_bits", c_int),
        ("opposite_endian", c_bool),
    ]


class AudioInfo(Structure):
    """
    Start of sox_format_t as per source (1)


    (1) https://sourceforge.net/p/sox/code/ci/master/tree/src/sox.h#l1500
    """

    _fields_ = [
        ("filename", c_char_p),
        ("signal", SignalInfo),
        ("encoding", EncodingInfo),
    ]


soxopen = libsox.sox_open_read
soxopen.restype = POINTER(AudioInfo)
soxclose = libsox.sox_close


def dictify(it):
    """Convert structure into a dict"""
    if isinstance(it, bytes):
        return it.decode()
    if isinstance(it, (int, str, bool, float)) or it is None:
        return it
    keys = [k for k in dir(it) if "_" != k[0]]
    return {k: dictify(getattr(it, k)) for k in keys}


def get_audioinfo(fn):
    ret = soxopen(fn.encode(), None, None, None)
    if ret:
        retval = dictify(ret.contents)
    soxclose(ret)
    return retval


def get_duration(signal):
    return signal.length / max(signal.channels, 1) / max(signal.rate, 1)
