"""ppach: read-only Phoenix Point achievement and save inspector.

Run through bin/ppach. Nothing here writes to the game's or Steam's files;
the only writes are index caches under PPACH_CACHE (default ~/.cache/ppach).
"""
import argparse
import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ppach import gamedata, objgraph, paths, saves, steamkv, zsav  # noqa: E402

CLASS_CODES = ['as', 'he', 'sn', 'te', 'in', 'pr', 'be']
CLASS_NAMES = dict(zip(CLASS_CODES, ['Assault', 'Heavy', 'Sniper', 'Technician',
                                     'Infiltrator', 'Priest', 'Berserker']))


def _json(v):
    json.dump(v, sys.stdout, indent=1, default=str)
    print()


def cmd_paths(a):
    print('saves      ', paths.save_dir())
    print('game data  ', paths.game_data())
    try:
        schema, user = paths.steam_stats()
        print('steam stats', user)
    except SystemExit as e:
        print('steam stats', e)
    print('cache      ', paths.cache_dir())


def cmd_steam(a):
    schema, user = paths.steam_stats()
    s = steamkv.load(schema)[paths.APP_ID]['stats']
    u = steamkv.load(user).get('cache', {})
    rows, stats = [], {}
    for sid, v in s.items():
        if 'bits' not in v:
            stats[v.get('name')] = u.get(sid, {}).get('data')
            continue
        data = u.get(sid, {}).get('data', 0)
        for bit, ach in v['bits'].items():
            disp = ach['display']
            name = disp['name'].get('english') if isinstance(disp['name'], dict) else disp['name']
            desc = disp['desc'].get('english') if isinstance(disp['desc'], dict) else disp['desc']
            prog = ach.get('progress')
            rows.append(((data >> int(bit)) & 1, name, desc, prog))
    got = sum(r[0] for r in rows)
    print('Steam: %d of %d achievements earned' % (got, len(rows)))
    for done, name, desc, prog in sorted(rows, key=lambda r: r[0]):
        if done and not a.all:
            continue
        extra = ''
        if prog:
            st = prog['value']['operand1']
            extra = '  [%s/%s]' % (stats.get(st, '?'), prog['max_val'])
        print('  %s %s: %s%s' % ('x' if done else ' ', name, desc, extra))
    if not a.all:
        print('(Steam counters lag the game; use `ppach progress` for exact lists.)')


def cmd_progress(a):
    with open(paths.options_file()) as f:
        opts = objgraph.top_level(json.load(f))
    guids = gamedata.guids()
    req = gamedata.required()
    report = {}
    for key, need in req.items():
        have_raw = opts.get(key) or []
        have = {x if isinstance(x, str) else guids.get(objgraph.guid(x), objgraph.guid(x))
                for x in have_raw}
        report[key] = (len(set(need) & have), len(need), [n for n in need if n not in have])
    combos = {','.join(sorted(p)) for p in itertools.combinations(CLASS_CODES, 2)}
    have = {','.join(sorted(x.split(','))) for x in opts.get('Achievement_AllClassCombo') or []}
    missing = sorted(combos - have)
    report['Achievement_AllClassCombo'] = (
        len(combos & have), len(combos),
        [' + '.join(CLASS_NAMES[c] for c in m.split(',')) for m in missing])
    if a.json:
        _json({k: {'have': h, 'need': n, 'missing': m} for k, (h, n, m) in report.items()})
        return
    print('Progress across all saves (%s):' % paths.options_file())
    for key, (h, n, miss) in report.items():
        print('  %-36s %3d/%-3d%s' % (key.replace('Achievement_', ''), h, n,
                                       '' if miss else '  done'))
        for m in miss:
            print('      missing: %s' % m)
    flags = sorted(k.replace('Achievement_', '') for k, v in opts.items()
                   if k.startswith('Achievement_') and v is True)
    print('  flags set: %s' % ', '.join(flags))
    print('Options.jopt is written lazily; very recent actions may not show yet.')


def _filter(rows, a):
    if getattr(a, 'campaign', None):
        rows = [r for r in rows if r['campaign'].startswith(a.campaign)]
    return rows


def cmd_saves(a):
    rows = _filter(saves.scan(), a)
    if a.geoscape:
        rows = [r for r in rows if not r['tactical']]
    rows = rows[-a.last:] if a.last else rows
    if a.json:
        return _json(rows)
    print('%-34s %-16s %-16s %-8s %-8s %s' % ('save', 'saved', 'in-game', 'campaign', 'level', 'kind'))
    for r in rows:
        print('%-34s %-16s %-16s %-8s %-8s %s' % (
            r['file'][:34], r['saved'], r['ingame'], r['campaign'], r['difficulty'],
            'tactical' if r['tactical'] else 'geoscape'))


def cmd_campaigns(a):
    groups = {}
    for r in saves.scan():
        groups.setdefault(r['campaign'], []).append(r)
    print('%-8s %-8s %5s  %-16s %-16s %s' % ('campaign', 'level', 'saves', 'in-game from', 'in-game to', 'last saved'))
    for c, rs in sorted(groups.items(), key=lambda kv: kv[1][-1]['saved']):
        dates = sorted(r['ingame'] for r in rs)
        print('%-8s %-8s %5d  %-16s %-16s %s' % (c, rs[-1]['difficulty'], len(rs), dates[0],
                                                dates[-1], rs[-1]['saved']))


def _one(name):
    return saves.scan(full=True, names=[paths.save_path(name)])[0]


def cmd_save(a):
    s = _one(a.name)
    if a.json:
        return _json(s)
    print('%s: campaign %s, %s, in-game %s, saved %s%s' % (
        s['file'], s['campaign'], s['difficulty'], s['ingame'], s['saved'],
        ' (tactical: no geoscape state)' if s['tactical'] else ''))
    if s['tactical']:
        return
    print('relations:', ', '.join('%s %s' % kv for kv in sorted(s['relations'].items())))
    wars = [k for k, v in s['war'].items() if v]
    print('at war:   ', ', '.join(sorted(wars)) or 'none')
    print('population:', ', '.join('%s %d' % kv for kv in sorted(s['population'].items())))
    v = s['vars']
    shown = v if a.vars else {k: x for k, x in v.items() if x}
    print('variables:', ', '.join('%s=%s' % kv for kv in sorted(shown.items())))
    print('last %d events:' % a.events)
    for e in s['events'][-a.events:]:
        print('  %s  %-28s choice %s' % (e['at'], e['id'], e['choice']))


def cmd_events(a):
    s = _one(a.name)
    if s['tactical']:
        raise SystemExit('tactical saves do not hold event records; use a geoscape save')
    rx = re.compile(a.match) if a.match else None
    data = gamedata._read_bytes() if a.text else None
    for e in s['events']:
        if rx and not rx.search(e['id']):
            continue
        line = '%s  %-30s choice %s' % (e['at'], e['id'], e['choice'])
        if data is not None and e['choice'] is not None:
            t = gamedata.english('%s_CHOICE_%s_TEXT' % (e['id'], e['choice']), data)
            line += '  ' + (t or '').replace('\n', ' ')[:100]
        print(line)


def cmd_timeline(a):
    rows = [r for r in _filter(saves.scan(), a) if not r['tactical']]
    full = saves.scan(full=True, names=[paths.save_path(r['file']) for r in rows])
    full.sort(key=lambda r: (r['ingame'], r['saved']))
    rels = a.rel or ['SY>PX', 'AN>PX', 'NJ>PX']
    print('%-16s %-30s %s' % ('in-game', 'save', '  '.join(rels + (a.var or []) + ['war'])))
    for r in full:
        cells = ['%*s' % (len(x), r['relations'].get(x, '-')) for x in rels]
        cells += ['%*s' % (len(x), r['vars'].get(x, 0)) for x in a.var or []]
        cells.append(','.join(sorted(k for k, v in r['war'].items() if v)) or '-')
        print('%-16s %-30s %s' % (r['ingame'], r['file'][:30], '  '.join(cells)))


def cmd_def(a):
    assets = gamedata.Assets()
    names = [n for n in assets.byname if n == a.name] or \
        sorted(n for n in assets.byname if a.name.lower() in n.lower())
    if len(names) != 1:
        print('\n'.join(names[:200]) or 'no match')
        return
    b = assets.raw(assets.byname[names[0]])
    print('==', names[0], '(%d bytes)' % len(b))
    data = gamedata._read_bytes()
    for s in dict.fromkeys(x.decode() for x in re.findall(rb'[\x20-\x7e]{4,}', b)):
        # Localization keys: KEY_* for items, <EVENT>_TITLE / _CHOICE_n_TEXT for events.
        t = gamedata.english(s, data) if re.fullmatch(r'[A-Z][A-Z0-9_]*_[A-Z0-9_]+', s) else None
        if t:
            print('  %s = %s' % (s, t.replace('\n', ' ')[:300]))
        else:
            print('  ' + s)
    for r in dict.fromkeys(assets.refs(b)):
        print('  -> ' + r)


def cmd_text(a):
    data = gamedata._read_bytes()
    for k in a.keys:
        print('%s = %s' % (k, gamedata.english(k, data)))


def cmd_dump(a):
    d = zsav.load(paths.save_path(a.name), {a.section})
    if a.section in ('Contents', 'Metadata'):
        _json(objgraph.top_level(d, a.section))
    else:
        _json(d[a.section])


def cmd_version(a):
    """Game version, owned DLCs and OS, for bug reports (no personal ids)."""
    import platform
    for log in paths.player_logs():
        text = open(log, encoding='utf8', errors='replace').read()
        m = re.search(r'"app_version":"([^"]+)","platform":"([^"]+)"', text)
        if not m:
            continue
        print('game     ', m.group(1), '(%s)' % m.group(2))
        dlc = re.search(r'"BoughtDLCs":\[([^\]]*)\]', text)
        if dlc:
            names = [re.sub('EntitlementDef$', '', x.strip('"')) for x in dlc.group(1).split(',') if x]
            print('DLCs     ', ', '.join(names) or '-')
        u = re.search(r'Initialize engine version: (\S+)', text)
        if u:
            print('Unity    ', u.group(1))
        break
    else:
        print('game      version not found; start the game once (it writes Player.log)')
    if platform.system() == 'Darwin':
        print('OS        macOS', platform.mac_ver()[0])
    else:
        print('OS       ', platform.platform())


def cmd_cloud(a):
    cache = paths.cloud_cache()
    d = paths.save_dir()
    kv = steamkv.load_text(cache)[paths.APP_ID]
    cloud = {os.path.basename(k): v for k, v in kv.items() if isinstance(v, dict)}
    local = {f for f in os.listdir(d) if f.endswith('.zsav')}
    if not a.keep:
        print('%s (ChangeNumber %s)' % (cache, kv.get('ChangeNumber')))
        size = sum(int(v.get('size', 0)) for v in cloud.values())
        print('cloud: %d files, %.0f MB; local saves: %d, %d of them not in the cloud'
              % (len(cloud), size / 1e6, len(local), len(local - set(cloud))))
        unsynced = [f for f, v in cloud.items() if v.get('syncstate') != '1']
        gone = [f for f in cloud if not os.path.exists(os.path.join(d, f))]
        if unsynced:
            print('not synced:', ' '.join(sorted(unsynced)))
        if gone:
            print('in the cloud but not local:', ' '.join(sorted(gone)))
        if a.list:
            for f in sorted(cloud):
                print('  ' + f)
        return
    with open(a.keep) as f:
        keep = {l.strip() + ('' if l.strip().endswith('.zsav') else '.zsav')
                for l in f if l.strip() and not l.startswith('#')}
    missing = keep - local
    if missing:
        raise SystemExit('keep-list saves not found: %s' % ' '.join(sorted(missing)))
    doomed = sorted(local - keep)
    if a.paths:
        for f in doomed:
            print(os.path.join(d, f))
        return
    size = sum(os.path.getsize(os.path.join(d, f)) for f in doomed)
    print('keep %d saves; would delete %d (%.2f GB), %d of them also in Steam Cloud'
          % (len(keep), len(doomed), size / 1e9, len(set(doomed) & set(cloud))))
    print('kept but local-only: %s' % (' '.join(sorted(keep - set(cloud))) or '-'))


def main(argv=None):
    p = argparse.ArgumentParser(prog='ppach', description=__doc__.split('\n')[0])
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('paths', help='show discovered file locations')
    s = sub.add_parser('steam', help='Steam achievements (from the local stats cache)')
    s.add_argument('--all', action='store_true', help='also list earned ones')
    s = sub.add_parser('progress', help='cross-save lists in Options.jopt vs. game requirements')
    s.add_argument('--json', action='store_true')
    s = sub.add_parser('saves', help='list saves with campaign, difficulty and in-game date')
    s.add_argument('--campaign')
    s.add_argument('--last', type=int)
    s.add_argument('--geoscape', action='store_true', help='skip tactical saves')
    s.add_argument('--json', action='store_true')
    sub.add_parser('campaigns', help='one line per campaign')
    s = sub.add_parser('save', help='relations, wars, variables and recent events in one save')
    s.add_argument('name')
    s.add_argument('--events', type=int, default=15)
    s.add_argument('--vars', action='store_true', help='include zero-valued variables')
    s.add_argument('--json', action='store_true')
    s = sub.add_parser('events', help='event records (story choices) in a geoscape save')
    s.add_argument('name')
    s.add_argument('--match', help='regex on the event id, e.g. "PROG_SY|CHAIN_NJ"')
    s.add_argument('--text', action='store_true', help='show the English text of each choice')
    s = sub.add_parser('timeline', help='relations/variables across a campaign\'s geoscape saves')
    s.add_argument('--campaign', required=True)
    s.add_argument('--rel', action='append', help='e.g. SY>PX or AN>SY (repeatable)')
    s.add_argument('--var', action='append', help='story variable, e.g. Polyphonic (repeatable)')
    s = sub.add_parser('def', help='inspect a game definition (needs `ppach setup`)')
    s.add_argument('name', help='exact def name or a substring to search for')
    s = sub.add_parser('text', help='English text for localization keys')
    s.add_argument('keys', nargs='+')
    s = sub.add_parser('dump', help='decoded JSON of one section of a save')
    s.add_argument('name')
    s.add_argument('--section', default='Metadata',
                   help='Metadata (default), Contents, Geoscape, LevelParams, ...')
    sub.add_parser('version', help='game version, DLCs and OS (for bug reports)')
    s = sub.add_parser('cloud', help='Steam Cloud status, or a prune plan for a keep list')
    s.add_argument('--list', action='store_true', help='list the cloud-tracked files')
    s.add_argument('--keep', help='file with one save name per line; report what pruning would delete')
    s.add_argument('--paths', action='store_true', help='with --keep: print full paths of the saves to delete')
    a = p.parse_args(argv)
    globals()['cmd_' + a.cmd](a)


if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError:
        pass
