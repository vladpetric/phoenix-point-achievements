"""Decoder for Phoenix Point .zsav save files.

A .zsav is gzip over a tagged binary object graph:

    'O' + 8 header bytes, then top-level fields until the name table.
    0x0e <int32 field id>            field name = name_table[id]
    0x01 null   0x02 bool   0x03-0x05 byte   0x06/0x07 int16/uint16
    0x08/0x09 int32/uint32  0x0a/0x0b int64/uint64  0x0c float  0x0d double
    0x0f <int32 total len> <7-bit len> utf8      string
    0x10 <int32 byte len> values...              list
    0x11 <int32 byte len> (0x0e id, value)...    object

The field-name table at the end is a run of 0x0f strings that reaches EOF
exactly; it is found by scanning backwards for such a run.
"""
import gzip
import struct

_FIXED = {0x02: 1, 0x03: 1, 0x04: 1, 0x05: 1, 0x06: 2, 0x07: 2, 0x08: 4,
          0x09: 4, 0x0a: 8, 0x0b: 8, 0x0c: 4, 0x0d: 8}
_FMT = {0x06: '<h', 0x07: '<H', 0x08: '<i', 0x09: '<I', 0x0a: '<q',
        0x0b: '<Q', 0x0c: '<f', 0x0d: '<d'}


def name_table(b):
    def run_end(k):
        while k < len(b) and b[k] == 0x0f:
            n = struct.unpack_from('<I', b, k + 1)[0]
            if n < 5 or n > 300:
                return k
            k += 1 + n
        return k
    start = None
    for k in range(len(b) - 6, max(0, len(b) - 600000), -1):
        if b[k] == 0x0f and run_end(k) == len(b):
            start = k
    if start is None:
        raise ValueError('field-name table not found')
    names, k = [], start
    while k < len(b):
        n = struct.unpack_from('<I', b, k + 1)[0]
        names.append(b[k + 6:k + 1 + n].decode('utf8', 'replace'))
        k += 1 + n
    return start, names


class _Reader:
    def __init__(self, b, names):
        self.b, self.names = b, names

    def skip(self, k):
        t = self.b[k]
        if t == 0x01:
            return k + 1
        if t in _FIXED:
            return k + 1 + _FIXED[t]
        if t in (0x0f, 0x10, 0x11):
            return k + 1 + struct.unpack_from('<I', self.b, k + 1)[0]
        raise ValueError('tag %#x at %d' % (t, k))

    def value(self, k):
        b, t = self.b, self.b[k]
        k += 1
        if t == 0x01:
            return None, k
        if t == 0x02:
            return bool(b[k]), k + 1
        if t in (0x03, 0x04, 0x05):
            return b[k], k + 1
        if t in _FMT:
            return struct.unpack_from(_FMT[t], b, k)[0], k + _FIXED[t]
        if t == 0x0f:
            end = k + struct.unpack_from('<I', b, k)[0]
            j, n, shift = k + 4, 0, 0
            while True:
                c = b[j]
                j += 1
                n |= (c & 0x7f) << shift
                shift += 7
                if c < 0x80:
                    break
            return b[j:j + n].decode('utf8', 'replace'), end
        if t == 0x10:
            end = k + struct.unpack_from('<I', b, k)[0]
            k += 4
            out = []
            while k < end:
                v, k = self.value(k)
                out.append(v)
            return out, k
        if t == 0x11:
            end = k + struct.unpack_from('<I', b, k)[0]
            k += 4
            out = {}
            while k < end:
                if b[k] != 0x0e:
                    raise ValueError('expected field at %d' % k)
                f = struct.unpack_from('<i', b, k + 1)[0]
                v, k = self.value(k + 5)
                out[self.names[f]] = v
            return out, k
        raise ValueError('tag %#x at %d' % (t, k - 1))


def load(path, only=None):
    """Decode a save. `only` limits decoding to the named top-level fields
    (for example {'Metadata'}); the others are skipped by length."""
    opener = gzip.open if path.endswith('.zsav') else open
    with opener(path, 'rb') as f:
        b = f.read()
    start, names = name_table(b)
    r = _Reader(b, names)
    out, k = {}, 9
    while k < start and b[k] == 0x0e:
        name = names[struct.unpack_from('<i', b, k + 1)[0]]
        k += 5
        if only is None or name in only:
            out[name], k = r.value(k)
        else:
            k = r.skip(k)
    return out
