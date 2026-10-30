# Phoenix Point achievement tools

A read-only command-line tool (`ppach`) and a Claude Code skill for chasing
100% achievements in [Phoenix Point](https://store.steampowered.com/app/839770/)
(Steam). It decodes the game's save files and cross-save progress file, so
you can see exactly what is missing and which save to reload for a story
choice or ending.

- `ppach progress` lists which items, research, abilities, endings,
  facilities, alien captures and class pairs you still need for the
  "do everything" achievements. It uses the game's own lists, not a wiki.
- `ppach steam` shows which Steam achievements are still locked.
- `ppach campaigns`, `saves`, `save`, `events` and `timeline` show
  relations, wars, story variables and the choices you made in each save.
- `ppach version` prints the game version, owned DLCs and OS for bug
  reports.
- `ppach cloud` shows what Steam Cloud holds, and with `--keep <file>`
  which saves pruning down to a keep list would delete.
- `ppach def` and `ppach text` show game definitions and their English
  text, such as what each event choice does.

[`skills/phoenix-point-achievements/game-notes.md`](skills/phoenix-point-achievements/game-notes.md)
collects what this turned up: the Project Vulture chain for Master Scientist,
how the two Synedrion endings are decided, and the three turret magazines
that Master Manufacturer requires but the game never lets you build.

## Safety

`ppach` never writes to the game's, Steam's or your save files. Its only
writes are caches in `~/.cache/ppach` (or `$PPACH_CACHE`). Delete that
directory at any time.

To delete old saves, delete the files from `ppach cloud --keep <file>
--paths` while the game is running at its main menu, then quit the game:
Steam Cloud syncs only when the game starts and exits, and saves deleted
while the game is closed can be downloaded again.

## Requirements

- macOS with the Steam version of Phoenix Point. Other platforms should work
  if you point the environment variables below at the right files, but only
  macOS has been tested.
- Python 3.9 or later. Most commands use only the standard library.
- `ppach progress` and `ppach def` need [UnityPy](https://pypi.org/project/UnityPy/)
  to read the game's definitions. `ppach setup` installs it into a private
  virtual environment in the cache directory.

## Install

    git clone <this repository> ~/phoenix-point-achievements
    ~/phoenix-point-achievements/install.sh   # links ppach and the Claude skill
    ppach setup                               # optional: UnityPy for progress/def

`install.sh` symlinks `bin/ppach` into `~/.local/bin` and the skill into
`~/.claude/skills`. It refuses to replace anything that isn't already one of
its own links. You can also run `bin/ppach` directly without installing.

## Examples

    ppach steam
    ppach progress
    ppach campaigns
    ppach saves --last 10 --geoscape
    ppach save Geoscape_04_02_2047
    ppach events Geoscape_04_02_2047 --match 'PROG_SY|CHAIN_NJ' --text
    ppach timeline --campaign 1a2b3c4d --rel 'SY>PX' --rel 'AN>SY' --var Polyphonic --var Terraformers
    ppach def PROG_SY3_WIN
    ppach text KEY_ARMADILLO_NAME
    ppach cloud --keep keep.txt

Faction codes: `PX` Phoenix, `NJ` New Jericho, `SY` Synedrion, `AN` Disciples
of Anu. Quote `SY>PX`-style arguments, or the shell treats `>` as a redirect.
Difficulty names follow the game's menu: Rookie, Veteran, Hero, Legend.

## Configuration

| Variable | Default (macOS) |
|---|---|
| `PPACH_SAVE_DIR` | newest `~/Library/Application Support/com.snapshotgames.phoenixpoint/Steam/<id>/` |
| `PPACH_STEAM_DIR` | `~/Library/Application Support/Steam` |
| `PPACH_GAME_DATA` | `$PPACH_STEAM_DIR/steamapps/common/Phoenix Point/PhoenixPointOSX.app/Contents/Resources/Data/sharedassets0.assets` |
| `PPACH_CACHE` | `~/.cache/ppach` |

## Layout

    bin/ppach                    wrapper: picks the venv's Python if present
    ppach/                       Python package (cli, save decoder, game data, Steam stats)
    skills/phoenix-point-achievements/
        SKILL.md                 Claude Code skill
        game-notes.md            achievement mechanics and blockers
        file-formats.md          .zsav / Options.jopt / assets formats
        bug-reports/             example report for the developers
        fixes/                   Options.jopt fix for Master Manufacturer
    install.sh
    LICENSE                      MIT

## License

MIT; see [LICENSE](LICENSE).

Phoenix Point is a trademark of Snapshot Games. This project is not
affiliated with or endorsed by Snapshot Games.
