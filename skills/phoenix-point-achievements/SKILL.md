---
name: phoenix-point-achievements
description: Track Phoenix Point (Steam app 839770) achievement progress and investigate save files with the read-only `ppach` tool. Use when the user asks what achievements are left, why one has not unlocked, which save to reload for a story choice or ending, how a campaign is going (relations, wars, story variables, events), or what a game definition or event choice does.
---

# Phoenix Point achievements

`ppach` reads the game's saves, `Options.jopt`, the game's definitions and
Steam's local stats and cloud caches. It never writes to any of them; it only writes
index caches under `~/.cache/ppach`. Run `ppach setup` once to install
UnityPy, which `progress` and `def` need.

Background: [game-notes.md](game-notes.md) (achievement mechanics, story
chains, known blockers) and [file-formats.md](file-formats.md).

## Commands

| Question | Command |
|---|---|
| What is left on Steam? | `ppach steam` |
| Exactly which items, research, abilities, endings, class pairs are missing? | `ppach progress` |
| Which campaigns exist, at what difficulty? | `ppach campaigns` |
| Recent saves | `ppach saves --last 10` (add `--campaign <id>`, `--geoscape`) |
| State of one save | `ppach save <name>` (relations, wars, population, variables, last events) |
| Story choices made | `ppach events <name> --match 'PROG_SY\|CHAIN_NJ' --text` |
| Find a save to reload | `ppach timeline --campaign <id> --rel 'SY>PX' --var Polyphonic` |
| What does a def / event do? | `ppach def <name or substring>` (strings, English texts, referenced defs) |
| Localized text | `ppach text KEY_...` |
| Raw decoded data | `ppach dump <name> --section Metadata\|Contents` |
| Game version, DLCs, OS (for bug reports) | `ppach version` |
| Steam Cloud status | `ppach cloud` (add `--list`) |
| What would pruning to a keep list delete? | `ppach cloud --keep <file>` (add `--paths` for the delete list) |

Save names are the file name without `.zsav`. Quote relation names: an
unquoted `SY>PX` is a shell redirect.

## Workflows

**Progress check.** Run `ppach steam` and `ppach progress`. If a recent
in-game action is missing from `progress`, say `Options.jopt` is written
lazily and offer to re-check after the user saves and quits to the menu.

**Find a save to reload.** Identify the campaign (`ppach campaigns`), then
use `timeline` for the relations and variables that matter, and `events
--text` on candidates to confirm which story choices are still ahead. Only
geoscape saves hold story state. Report the save's file name, the real-world
time it was saved and its in-game date so the user can find it in the
game's load screen.

**Explain an event or requirement.** `ppach def <EVENT>_GeoscapeEventDef`
shows each choice's text and the variables it touches. Check
[game-notes.md](game-notes.md) first; it covers the Project Vulture chain,
the Synedrion ending split and the unbuildable turret magazines.

**Prune saves.** Hundreds of saves make the game's save and load screens
slow. Propose a keep list per campaign before deleting anything:

- the current campaign: latest autosave, the last mission's save chain, two
  or three recent geoscape saves and the user's named saves;
- any save the notes recommend for an open achievement (for example the
  Synedrion fork saves; check `ppach progress` for what is still open);
- a few geoscape saves just before the final mission of finished campaigns,
  and the latest saves of campaigns with an ending still to win.

Confirm each candidate with `ppach save` / `events`, write the keep list (one
save name per line) to the scratchpad, and show `ppach cloud --keep <file>`.
Then delete only after the user says so, in this order, because Steam Cloud
syncs this game only when the game starts and exits:

1. The user starts Phoenix Point and stays at the main menu. Check with
   `pgrep -il phoenix`.
2. Delete the files from `ppach cloud --keep <file> --paths` (recheck the
   plan first; the user may have saved since).
3. The user quits the game normally. Steam then removes the deleted saves
   from the cloud and uploads kept saves that were local-only.
4. Run `ppach cloud`: the file count should drop and nothing should be
   listed as not synced or missing locally. Have the user start the game
   once more to confirm deleted saves did not come back.

Deleting with the game closed risks Steam downloading the cloud copies
again on the next launch. Turning Steam Cloud off doesn't help: the cloud
copies stay and return when it is turned back on.

**Write a bug report for the developers.** When an achievement or item turns
out to be blocked by the game itself, draft a report the user can send as
their own. Example: [bug-reports/master-manufacturer-turret-magazines.md](bug-reports/master-manufacturer-turret-magazines.md).

- Write in the first person, as the user: plain, friendly, specific. A
  subject line, what they were trying to do, the exact blocker, steps to
  reproduce, expected result, setup, an offer of supporting files, thanks.
- Name the affected defs by their internal names (from `ppach progress`
  and `ppach def`) next to their English names, and cite the evidence (tags,
  list sizes, what the UI shows).
- Take the setup from `ppach version` (game version, DLCs, OS). Never
  include Steam ids, account ids, device ids or file paths with them.
- Include only what was actually checked. Drop claims you can't back up,
  and tell the user which statements they should verify in the game before
  sending.
- Write it to `~/phoenix-point-<topic>-bug.md` and add a copy to
  `bug-reports/` here.
- Where to send it (checked 2026-10-29; re-check if it matters):
  - Email `contact@snapshotgames.com`, listed on https://phoenixpoint.info/support
    (the page also mentions a contact form). Best for a formal report with
    attachments.
  - Discord https://discord.gg/PhoenixPoint; a 2023 changelog pointed bug
    reports to its `#bug_reporting` channel.
  - Steam "Bug and Technical Issue Discussion":
    https://steamcommunity.com/app/839770/discussions/4/ (public record;
    other players can confirm).
  - Also: https://forums.snapshotgames.com (no bug category) and
    https://www.reddit.com/r/PhoenixPoint/. The old in-game F12 reporter
    dates from 2018-19 and may be gone; Canny feedback was closed.
- Outcome of the Master Manufacturer report: the unmodded game is no longer
  supported, and players pointed to the Terror from the Void mod. So a report
  documents the bug, but don't count on a patch; offer the edit below.

**Fix a blocked list achievement by editing `Options.jopt`.** Do this only when
the user asks for it, and after the blocker has been shown to be the game's
fault, not a missing in-game step. The worked example is Master Manufacturer:
the steps are in [game-notes.md](game-notes.md) and the script is
[fixes/master-manufacturer-add-magazines.py](fixes/master-manufacturer-add-magazines.py).

1. Check that the game is closed (`pgrep -il phoenix` prints nothing).
2. Copy `Options.jopt` to a dated backup folder and record its SHA-256.
   Keep the backup out of the save folder, which Steam Cloud syncs.
3. Take each missing def's GUID from the ppach GUID cache, and take its C#
   class from the game data, by comparing script ids with a def already on
   the list. Don't infer the class from the def's folder.
4. Run a dry run, then `--apply`. The script must refuse a file that has
   changed since the backup or doesn't round-trip byte-exact.
5. Verify with `ppach progress`. Steam awarded the achievement at the next
   launch without the user doing anything; confirm it with `ppach steam`.
6. After the game has saved again, compare the *resolved* content with
   `objgraph.top_level`, not the bytes: the game renumbers object ids.

## Rules

- Treat saves and `Options.jopt` as the user's data. Do not edit them unless
  the user explicitly asks, and then only with the game closed and a backup
  made first. Steam Cloud syncs `Options.jopt`, so an edit can propagate.
  Deleting saves is the exception covered by **Prune saves** above: only on
  the user's go-ahead, and with the game at its main menu, not closed.
- Do not claim something can be done in the UI without evidence; the turret
  magazines are tagged manufacturable but cannot be built.
- Don't treat a tactical save as proof of story state. Use the geoscape save
  before or after it.
