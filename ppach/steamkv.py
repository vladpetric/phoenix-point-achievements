"""Reader for Steam's binary KeyValues files (appcache/stats/*.bin)."""
import struct


def _parse(b, i=0):
    d = {}
    while True:
        t = b[i]
        i += 1
        if t in (8, 11):
            return d, i
        j = b.index(0, i)
        key = b[i:j].decode('utf8', 'replace')
        i = j + 1
        if t == 0:
            v, i = _parse(b, i)
        elif t == 1:
            j = b.index(0, i)
            v = b[i:j].decode('utf8', 'replace')
            i = j + 1
        elif t in (2, 4, 6):
            v = struct.unpack_from('<i', b, i)[0]
            i += 4
        elif t == 3:
            v = struct.unpack_from('<f', b, i)[0]
            i += 4
        elif t == 7:
            v = struct.unpack_from('<Q', b, i)[0]
            i += 8
        elif t == 10:
            v = struct.unpack_from('<q', b, i)[0]
            i += 8
        else:
            raise ValueError('KeyValues type %d at %d' % (t, i))
        d[key] = v


def load(path):
    with open(path, 'rb') as f:
        return _parse(f.read())[0]


def load_text(path):
    """Parse a text KeyValues file (e.g. userdata/.../remotecache.vdf)."""
    import re
    tokens = re.findall(r'"((?:[^"\\]|\\.)*)"|([{}])', open(path, encoding='utf8').read())
    stack, cur, key = [], {}, None
    for s, brace in tokens:
        if brace == '{':
            new = {}
            cur[key] = new
            stack.append(cur)
            cur, key = new, None
        elif brace == '}':
            cur = stack.pop()
        elif key is None:
            key = s
        else:
            cur[key], key = s, None
    return cur
