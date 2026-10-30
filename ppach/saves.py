"""Summaries of save files, cached per (file name, size, mtime)."""
import datetime
import glob
import json
import os
import sys
from multiprocessing import Pool

from ppach import gamedata, objgraph, paths, zsav

# Diplomacy parties are the same in every campaign.
PARTIES = {
    '4ffc3579-4ee1-ba14-88c5-27d14cff816c': 'PX',
    '975f0cbb-2dbc-b274-4b54-3d1479a989f4': 'NJ',
    'e1964d03-aad7-2a74-2a99-9876110748a0': 'SY',
    '744560d4-4747-a6a4-7848-833d06f64930': 'AN',
}
FACTIONS = {
    '8be7e872-0ad2-a2a4-7bee-c980ed304a8a': 'PX',
    'd31c78b9-ff0e-8b94-ab96-9672da73da54': 'NJ',
    '0e6dc218-e157-5954-c9ab-1a0606e0d914': 'SY',
    'edc6783a-be00-1a84-2b97-2fe1e0fc5448': 'AN',
}
DIFFICULTY = {'Easy': 'Rookie', 'Standard': 'Veteran', 'Hard': 'Hero', 'VeryHard': 'Legend'}
_VERSION = 2


def ticks(t):
    """.NET ticks (100 ns since 0001-01-01) -> 'YYYY-MM-DD HH:MM'."""
    return (datetime.datetime(1, 1, 1) + datetime.timedelta(microseconds=int(t) // 10)
            ).strftime('%Y-%m-%d %H:%M')


def metadata(d, guids):
    objs = objgraph.objects(d, 'Metadata')
    res = objgraph.resolver(objs)
    top = res([o for o in objs.values() if o.get('TopLevel')][0]['ObjectValue'])
    diff = guids.get(objgraph.guid(top.get('DifficultyDef')) or '', '')
    diff = diff.replace('_GameDifficultyLevelDef', '')
    return {
        'campaign': top['GameId']['_guidString'][:8],
        'ingame': ticks(top['IngameTime']['dateTime']['Ticks']),
        'saved': ticks(top['SaveCreated']['dateTime']['Ticks']),
        'name': top.get('Name'),
        'type': (top.get('SaveType') or {}).get('EnumName'),
        'tactical': bool(top.get('IsTacticalSave')),
        'difficulty': DIFFICULTY.get(diff, diff),
    }


def geoscape(d):
    """Relations, wars, story variables, population and event records."""
    objs = objgraph.objects(d)
    res = objgraph.resolver(objs)
    out = {'relations': {}, 'war': {}, 'vars': {}, 'population': {}, 'events': []}
    for o in objs.values():
        v = o.get('ObjectValue')
        if not isinstance(v, dict):
            continue
        if '_diplomacy' in v and '_thisParty' in v:
            a = PARTIES.get(objgraph.guid(res(v['_thisParty'])))
            b = PARTIES.get(objgraph.guid(res(v['_withParty'])))
            if a and b:
                out['relations'][a + '>' + b] = v['_diplomacy']
        if 'AtWar' in v and 'Relation' in v:
            r = res(v['Relation'])
            a = PARTIES.get(objgraph.guid(r.get('_thisParty')))
            b = PARTIES.get(objgraph.guid(r.get('_withParty')))
            if a and b:
                out['war'][a + '>' + b] = v['AtWar']
        if 'CustomVariables' in v:
            cv = res(v['CustomVariables'])
            out['vars'] = cv if isinstance(cv, dict) else {}
        if 'EncounterRecords' in v:
            out['events'] = [{'id': e['EventId'], 'choice': e.get('_selectedChoice'),
                              'at': ticks(e['FirstTriggerAt']['_time']['Ticks'])}
                             for e in res(v['EncounterRecords'])]
        sd = v.get('SerializationData')
        if isinstance(sd, dict) and isinstance(sd.get('HavenData'), dict):
            owner = objgraph.guid(res(sd.get('OwnerFactionDef')))
            k = FACTIONS.get(owner, (owner or '?')[:8])
            hd = res(sd['HavenData'])
            if isinstance(hd, dict) and isinstance(hd.get('Population'), (int, float)):
                out['population'][k] = out['population'].get(k, 0) + hd['Population']
    out['events'].sort(key=lambda e: e['at'])
    return out


def summarize(path, guids, full=True):
    d = zsav.load(path, None if full else {'Metadata'})
    s = {'file': os.path.basename(path)[:-5]}
    s.update(metadata(d, guids))
    if full and not s['tactical']:
        s.update(geoscape(d))
    return s


def _cache_key(path):
    st = os.stat(path)
    return '%s|%d|%d' % (os.path.basename(path), st.st_size, int(st.st_mtime))


_guids = None


def _init(guids):
    global _guids
    _guids = guids


def _work(args):
    path, full = args
    try:
        return summarize(path, _guids, full)
    except Exception as e:  # keep scanning; report the bad file
        return {'file': os.path.basename(path)[:-5], 'error': repr(e)[:200]}


def scan(full=False, names=None):
    """Summaries of every save (or of `names`), oldest first by save time."""
    kind = 'full' if full else 'meta'
    cpath = os.path.join(paths.cache_dir(), 'saves-%s-v%d.json' % (kind, _VERSION))
    try:
        with open(cpath) as f:
            cache = json.load(f)
    except (OSError, ValueError):
        cache = {}
    files = names or glob.glob(os.path.join(paths.save_dir(), '*.zsav'))
    keys = {p: _cache_key(p) for p in files}
    todo = [p for p in files if keys[p] not in cache]
    if todo:
        with Pool(min(8, os.cpu_count() or 1), _init, (gamedata.guids(),)) as pool:
            for p, s in zip(todo, pool.map(_work, [(p, full) for p in todo], chunksize=4)):
                if 'error' in s:
                    print('warning: %s: %s' % (s['file'], s['error']), file=sys.stderr)
                else:
                    cache[keys[p]] = s
        if not names:
            live = set(keys.values())
            cache = {k: v for k, v in cache.items() if k in live}
        tmp = cpath + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(cache, f)
        os.replace(tmp, cpath)
    out = [cache[keys[p]] for p in files if keys[p] in cache]
    return sorted(out, key=lambda s: s['saved'])
