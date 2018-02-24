import six
import zlib
from io import BytesIO


def compress(data_str, stream, encoding=None):
    if isinstance(data_str, six.string_types):
        if six.PY3:
            data_str = six.binary_type(data_str, encoding or 'utf-8')
        else:
            data_str = six.binary_type(data_str)
    res_buf = BytesIO(data_str)
    size = compress_stream(res_buf, stream)
    return dict(
        uncompressed_size=len(data_str),
        compressed_size=size
    )


def compress_stream(instr, outstr):
    co = zlib.compressobj(
        zlib.Z_BEST_COMPRESSION, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
    size = 0
    for chunk in instr:
        chunk = co.compress(chunk)
        size += len(chunk)
        outstr.write(chunk)

    chunk = co.flush()
    size += len(chunk)
    outstr.write(chunk)

    return size
