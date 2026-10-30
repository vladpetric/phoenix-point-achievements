"""Locate the game's save directory, game data and Steam stats.

Discovery covers the macOS Steam layout. On other systems set the
PPACH_* environment variables described in the README.
"""
import glob
import os
import re

APP_ID = '839770'
_MAC_SAVES = '~/Library/Application Support/com.snapshotgames.phoenixpoint/Steam'
_MAC_STEAM = '~/Library/Application Support/Steam'
_MAC_LOGS = '~/Library/Logs/Snapshot Games Inc/Phoenix Point'
_MAC_ASSETS = ('steamapps/common/Phoenix Point/PhoenixPointOSX.app/'
               'Contents/Resources/Data/sharedassets0.assets')


def _env(name):
    v = os.environ.get(name)
    return os.path.expanduser(v) if v else None


def cache_dir():
    d = _env('PPACH_CACHE') or os.path.join(
        _env('XDG_CACHE_HOME') or os.path.expanduser('~/.cache'), 'ppach')
    os.makedirs(d, exist_ok=True)
    return d


def save_dir():
    d = _env('PPACH_SAVE_DIR')
    if d:
        return d
    base = os.path.expanduser(_MAC_SAVES)
    found = [x for x in glob.glob(os.path.join(base, '*'))
             if os.path.isfile(os.path.join(x, 'Options.jopt'))]
    if not found:
        raise SystemExit('save directory not found; set PPACH_SAVE_DIR')
    # Several Steam accounts on one machine: use the most recently played.
    return max(found, key=lambda x: os.path.getmtime(os.path.join(x, 'Options.jopt')))


def options_file():
    return os.path.join(save_dir(), 'Options.jopt')


def steam_dir():
    return _env('PPACH_STEAM_DIR') or os.path.expanduser(_MAC_STEAM)


def game_data():
    p = _env('PPACH_GAME_DATA') or os.path.join(steam_dir(), _MAC_ASSETS)
    if not os.path.isfile(p):
        raise SystemExit('sharedassets0.assets not found; set PPACH_GAME_DATA')
    return p


def steam_stats():
    """Return (schema, user stats) paths from Steam's local stats cache."""
    d = os.path.join(steam_dir(), 'appcache', 'stats')
    schema = os.path.join(d, 'UserGameStatsSchema_%s.bin' % APP_ID)
    users = glob.glob(os.path.join(d, 'UserGameStats_*_%s.bin' % APP_ID))
    if not os.path.isfile(schema) or not users:
        raise SystemExit('Steam stats cache not found under %s; set PPACH_STEAM_DIR' % d)
    return schema, max(users, key=os.path.getmtime)


def cloud_cache():
    """Steam's Auto-Cloud tracking file for this game and save directory."""
    d = save_dir()
    acct = os.path.join(d, 'steam_autocloud.vdf')
    if not os.path.isfile(acct):
        raise SystemExit('no steam_autocloud.vdf in %s; Steam Cloud not in use' % d)
    m = re.search(r'"accountid"\s+"(\d+)"', open(acct).read())
    p = os.path.join(steam_dir(), 'userdata', m.group(1), APP_ID, 'remotecache.vdf')
    if not os.path.isfile(p):
        raise SystemExit('Steam Cloud cache not found: %s' % p)
    return p


def player_logs():
    """Unity Player.log files, newest first (the game rewrites them each run)."""
    d = _env('PPACH_LOG_DIR') or os.path.expanduser(_MAC_LOGS)
    logs = [os.path.join(d, f) for f in ('Player.log', 'Player-prev.log')]
    return [x for x in logs if os.path.isfile(x)]


def save_path(name):
    """Accept a bare save name, a file name, or a full path."""
    if os.path.sep in name and os.path.isfile(name):
        return name
    p = os.path.join(save_dir(), name)
    if not p.endswith('.zsav'):
        p += '.zsav'
    if not os.path.isfile(p):
        raise SystemExit('no such save: %s' % p)
    return p
