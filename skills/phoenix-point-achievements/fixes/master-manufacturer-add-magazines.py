"""Add the three unbuildable turret magazines to Options.jopt's
Achievement_ManufactureAllItems list (Master Manufacturer). Verified to work:
the achievement unlocked at the next game launch. See ../game-notes.md.

usage: python3 -I master-manufacturer-add-magazines.py OPTIONS_JOPT SHA256 [--apply]

Quit the game and copy Options.jopt to a backup first; SHA256 is the
backup's checksum, and the script refuses if the live file differs from it.
Without --apply it only prints what it would do. It refuses when a magazine
is already recorded, the file does not round-trip byte-exact, or the edit
would change anything besides the three objects and their list entries.
"""
import copy
import hashlib
import json
import os
import sys

ADD = [  # (def name, SerializationGuid) from the game's sharedassets0.assets
    ('NJ_TechTurretGun_AmmoClip_ItemDef', 'e5973e25-f53e-2104-cba9-3d17683a0be7'),
    ('NJ_PRCRTechTurretGun_AmmoClip_ItemDef', '48f69478-3e9c-ad04-78e0-a4f3a548ed78'),
    ('PX_LaserTechTurretGun_AmmoClip_ItemDef', '36189fcf-c197-7d74-e995-e86e578407ed'),
]
TYPE_NAME = 'PhoenixPoint.Tactical.Entities.Equipments.TacticalItemDef'
KEY = 'Achievement_ManufactureAllItems'


def die(msg):
    sys.exit('refused: ' + msg)


path, want_sha = sys.argv[1], sys.argv[2]
apply = sys.argv[3:] == ['--apply']
if sys.argv[3:] not in ([], ['--apply']):
    die('bad arguments')

raw = open(path, 'rb').read()
if hashlib.sha256(raw).hexdigest() != want_sha:
    die('Options.jopt changed since the backup was taken')
doc = json.loads(raw)
if json.dumps(doc, indent=2).encode() != raw:
    die('file does not round-trip byte-exact; refusing to rewrite it')

C = doc['Contents']
objs = {o['ObjectID']: o for o in C['Objects']}
if sorted(objs) != list(range(1, len(objs) + 1)) or [o['ObjectID'] for o in C['Objects']] != sorted(objs):
    die('object ids are not contiguous and in order')
top = [o for o in C['Objects'] if o.get('TopLevel')]
if len(top) != 1:
    die('expected exactly one top-level object')
entries = [e for e in top[0]['ObjectValue']['CollectionValues'] if e.get('Key') == KEY]
if len(entries) != 1:
    die('expected exactly one %s entry' % KEY)
lst = objs[entries[0]['Value']['ObjectID']]['ObjectValue']
types = {t['TypeName'].split(',')[0]: t['Id'] for t in C['Types']}
if TYPE_NAME not in types:
    die('type %s not in the file' % TYPE_NAME)
tid = types[TYPE_NAME]
have = {objs[r['ObjectID']]['ObjectValue'].get('SerializationGuid') for r in lst['CollectionValues']}
for name, g in ADD:
    if g in have:
        die('%s is already recorded' % name)

new = copy.deepcopy(doc)
NC = new['Contents']
nobjs = {o['ObjectID']: o for o in NC['Objects']}
nlst = nobjs[entries[0]['Value']['ObjectID']]['ObjectValue']['CollectionValues']
next_id = len(objs) + 1
for name, g in ADD:
    NC['Objects'].append({'ObjectID': next_id, 'TopLevel': False,
                          'ObjectValue': {'#Type': tid, 'SerializationGuid': g}})
    nlst.append({'ObjectID': next_id})
    print('add object %d  #Type %d  %s  %s' % (next_id, tid, g, name))
    next_id += 1
out = json.dumps(new, indent=2).encode()

# Independent check: the only differences are the three objects and three refs.
old_s = json.dumps(doc, sort_keys=True)
undo = copy.deepcopy(new)
undo['Contents']['Objects'] = undo['Contents']['Objects'][:-3]
{o['ObjectID']: o for o in undo['Contents']['Objects']}[entries[0]['Value']['ObjectID']]['ObjectValue']['CollectionValues'][-3:] = []
if json.dumps(undo, sort_keys=True) != old_s:
    die('internal check failed: the edit changed more than intended')
print('list grows %d -> %d; file %d -> %d bytes' % (len(nlst) - 3, len(nlst), len(raw), len(out)))

if not apply:
    print('dry run; pass --apply to write')
    sys.exit(0)
mode = os.stat(path).st_mode & 0o7777
tmp = path + '.ppach-edit.tmp'
with open(tmp, 'xb') as f:
    f.write(out)
    f.flush()
    os.fsync(f.fileno())
os.chmod(tmp, mode)
os.replace(tmp, path)
print('written; sha256 %s' % hashlib.sha256(out).hexdigest())
