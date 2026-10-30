"""Read definitions out of the game's sharedassets0.assets.

Two indexes are built once per game build and cached as JSON:

* guids: SerializationGuid -> def name. Found by a plain byte scan, because
  every def stores its name as a length-prefixed string shortly before a
  length-36 GUID string. Needs no third-party modules.
* required: the lists each "do everything" achievement checks. These are
  Unity PPtr arrays inside the AchievementDef MonoBehaviours, so reading
  them needs UnityPy (`ppach setup`).
"""
import json
import os
import re
import struct

from ppach import paths

_GUID = re.compile(rb'\x24\x00\x00\x00([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
                   rb'[0-9a-f]{4}-[0-9a-f]{12})')

# Options.jopt list key -> AchievementDef whose list it is checked against.
ACHIEVEMENT_LISTS = {
    'Achievement_ManufactureAllItems': 'ManufactureAllItems_AchievementDef',
    'Achievement_ResearchAllProjects': 'ResearchAllProjects_AchievementDef',
    'Achievement_UseAllAbilities': 'UseAbilities_AchievementDef',
    'Achievement_AllEndings': 'AllEndings_AchievementDef',
    'Achievement_BuildAllFacilities': 'BuildAllFacilities_AchievementDef',
    'Achievement_CaptureAllAlienTypes': 'CaptureAllAlienTypes_AchievementDef',
    'Achievement_RecruitAllClasses': 'RecruitAllClasses_AchievementDef',
    'Achievement_ReachAlliedWithAll': 'ReachAlliedAll_AchievementDef',
}


def _cache(kind):
    st = os.stat(paths.game_data())
    return os.path.join(paths.cache_dir(), '%s-%d-%d.json' % (kind, st.st_size, int(st.st_mtime)))


def _read_bytes():
    with open(paths.game_data(), 'rb') as f:
        return f.read()


def guids():
    p = _cache('guids')
    if os.path.isfile(p):
        with open(p) as f:
            return json.load(f)
    b = _read_bytes()
    out = {}
    for m in _GUID.finditer(b):
        g = m.group(1).decode()
        if g in out:
            continue
        s = m.start()
        name = None
        for pad in range(4):
            e = s - pad
            for n in range(1, 200):
                st = e - n
                if st < 4:
                    break
                if (struct.unpack_from('<I', b, st - 4)[0] == n and (n + pad) % 4 == 0
                        and all(32 <= c < 127 for c in b[st:e])):
                    name = b[st:e].decode()
                    break
            if name:
                break
        if name:
            out[g] = name
    with open(p, 'w') as f:
        json.dump(out, f)
    return out


def english(key, b=None):
    """English text for a localization key such as KEY_ARMADILLO_NAME.

    An entry is the string "Category/KEY", zero padding, an int32 language
    count, then one length-prefixed string per language, English first."""
    b = b if b is not None else _read_bytes()
    needle = b'/' + key.encode() + b'\x00'
    i = b.find(needle)
    while i >= 0:
        end = i + len(needle) - 1
        # The category starts after an int32 holding the string's length.
        if any(struct.unpack_from('<I', b, s - 4)[0] == end - s
               for s in range(max(4, i - 200), i)):
            k = end + (-end) % 4
            while k < end + 64 and struct.unpack_from('<I', b, k)[0] == 0:
                k += 4
            count, n = struct.unpack_from('<II', b, k)
            if 0 < count < 64 and 0 < n < 20000:
                return b[k + 8:k + 8 + n].decode('utf8', 'replace')
        i = b.find(needle, i + 1)
    return None


class Assets:
    """UnityPy view of sharedassets0 (MonoBehaviours by def name)."""

    def __init__(self):
        try:
            import UnityPy
        except ImportError:
            raise SystemExit('this command needs UnityPy; run `ppach setup` first')
        env = UnityPy.load(paths.game_data())
        self.objs = list(env.files.values())[0].objects
        p = _cache('bynames')
        if os.path.isfile(p):
            with open(p) as f:
                self.byname = json.load(f)
        else:
            self.byname = {}
            for pid, o in self.objs.items():
                if o.type.name == 'MonoBehaviour':
                    try:
                        self.byname[self.name_of(pid)] = pid
                    except Exception:
                        pass
            with open(p, 'w') as f:
                json.dump(self.byname, f)

    def raw(self, pid):
        return self.objs[pid].get_raw_data()

    def name_of(self, pid):
        b = self.raw(pid)
        n = struct.unpack_from('<I', b, 28)[0]
        return b[32:32 + n].decode()

    def refs(self, b):
        """Names of MonoBehaviours referenced by local PPtrs in raw bytes."""
        out = []
        for k in range(0, len(b) - 12, 4):
            fid, pid = struct.unpack_from('<iq', b, k)
            if fid == 0 and pid in self.objs and self.objs[pid].type.name == 'MonoBehaviour':
                try:
                    out.append(self.name_of(pid))
                except Exception:
                    pass
        return out

    def pptr_lists(self, b):
        """Every (count, PPtr...) array of local MonoBehaviours in raw bytes."""
        found = []
        for k in range(0, len(b) - 16, 4):
            n = struct.unpack_from('<I', b, k)[0]
            if not 1 <= n <= 1000 or k + 4 + 12 * n > len(b):
                continue
            names = []
            for i in range(n):
                fid, pid = struct.unpack_from('<iq', b, k + 4 + 12 * i)
                if fid != 0 or pid not in self.objs:
                    break
                try:
                    names.append(self.name_of(pid))
                except Exception:
                    break
            if len(names) == n:
                found.append(names)
        return found


def required():
    """{options key: [required def names]} for the list achievements."""
    p = _cache('required')
    if os.path.isfile(p):
        with open(p) as f:
            return json.load(f)
    a = Assets()
    out = {}
    for key, ach in ACHIEVEMENT_LISTS.items():
        b = a.raw(a.byname[ach])
        if key == 'Achievement_ResearchAllProjects':
            # Stored as research names, not references.
            names = list(dict.fromkeys(x.decode() for x in re.findall(rb'[A-Za-z0-9_]+_ResearchDef', b)))
        else:
            names = max(a.pptr_lists(b), key=len)
        out[key] = names
    with open(p, 'w') as f:
        json.dump(out, f, indent=1)
    return out
