---
name: phoenix-point-achievements
description: Track Phoenix Point (Steam app 839770) achievement progress and investigate save files with the read-only `ppach` tool. Use when the user asks what achievements are left, why one has not unlocked, which save to reload for a story choice or ending, how a campaign is going (relations, wars, story variables, events), or what a game definition or event choice does. Also use to write a bug report for the developers, to fix a cross-campaign achievement the game itself blocks by editing Options.jopt, and before changing the tool or skill, whose repository is public.
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

**Plan a campaign for a missing ending.** Read the ending's section in
[game-notes.md](game-notes.md), and check that the achievement def names no
difficulty (`ppach def AllEndings`). Then write a short checklist for the
user: difficulty, which faction to ally with, the exact choice texts (from
`ppach def <EVENT>_GeoscapeEventDef`), where to make a fork save, and when to
ask Claude for a check of variables. Base the main-research steps on
"Main story research to the final mission". Trace requirements with
`ppach def <Research>_ResearchDef` and its `_ExistingResearchRequirementDef_<n>`
defs, and take English names from `<Research>_ViewElementDef`. Save the
checklist where the user asks, by default `~/phoenix-point-<topic>-plan.md`.

A plan that depends on a comparison between variables (a tie, a lead of
one) must rest on the condition's operator, read from its raw bytes as
described in "Reading a condition's operator" in
[file-formats.md](file-formats.md). `ppach def` lists only the variable
names, and the order in which they are listed does not tell which operator
is used: one plan assumed a 2–2 tie went to Terraformation, and the run
locked in Polyphonic instead.

**Check an ending run in progress.** When the user asks for a score or
progress check on a run made from such a plan, read the plan first, then look
only at that campaign (by its difficulty in `ppach campaigns`; the user may
say to ignore the others):

1. `ppach saves --campaign <id> --last 40` and take the newest *geoscape*
   save (often a named one next to `autosave`). If the user played through
   a cloud-gaming service (such as GeForce Now), the saves reach this machine
   only after local Steam runs and syncs; when nothing new is on disk, say so
   and ask the user to start Steam, then list again. `pgrep -il phoenix` and
   `ppach cloud` tell whether it is synchronized; a few newest saves being
   local-only after a clean exit is normal.
2. `ppach save <name>` for variables and relations, and `ppach events <name>
   --match 'PROG_|CHAIN_' --text` for the story choices made so far. Compare
   the ending variables with the plan; a variable that never changed is
   absent from the list (= 0).
3. `ppach timeline --campaign <id> --rel 'SY>PX' --rel 'AN>SY' --rel 'AN>PX'
   --var <ending vars>` for trends. A steadily falling relation between two
   factions is the early warning for a war that can wreck the chosen ally.
4. Report: the score against the plan, story progress (the next story event
   and what triggers it, from `ppach def`), a relations table with trends, and
   short recommendations (the fork save, relation thresholds, research to
   rush, the next check-in).

Avoid `ppach dump --section Contents` for this: on a geoscape save it can
take minutes. Story events and `save` output are enough.

"Check the newest save" means the newest save of *any* campaign, so run
`ppach saves --last 8` without `--campaign`. When nothing is newer than the
last check, say so, and don't repeat the full report. Saves can show up
minutes after the time they carry: one check found no new saves, and
five minutes later saves stamped half an hour earlier were on disk (probably a
Steam Cloud download). So when the user says there should be a newer save, look
again rather than arguing from the earlier listing. A newest save that is
tactical shows no story state, so ask for a map save.

When the user names the fork and the after-choice saves ("there should be a
fork save and a post_choice save"), check both of them with `ppach save` and
`ppach events --match 'PROG_SY'`. The fork must be a geoscape save that has
the pre-choice score and no `<chain>_MISS` start for the deciding mission
yet. The after-choice save must show the `_WIN` event with the planned
choice text and the new score. Report the two side by side and accept the
user's own name for the fork (for example `fork_sy` for the plan's
`sy_fork`). Then offer a second copy of both outside the synced save folder:
Steam Cloud keeps only the newest saves, so a fork made early drops out of
the cloud. On a yes, copy them with `cp -p` into a dated folder under the
user's backup location, write `SHA256SUMS`, and compare those sums with the
originals. To restore, copy a save back into the save folder with the game
closed or at the main menu.

When the user reports that the ending event has fired ("I reached Liberty or
Death"), check that the event matches the plan's branch. If it doesn't,
read the condition operators before explaining anything (see above), say
plainly which ending this run now gives, and work out what each existing
fork save can still reach. Name the last geoscape save from before the
event (the only one that can still change the ending) and offer to back it
up together with the save where the ending locked.

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

When the user gives a name rule instead ("remove every save in campaign X
whose name lacks `good`"), the keep list is every save of the *other*
campaigns plus the matching saves in X: `--keep` deletes everything not on
the list, across all campaigns. Build it from `ppach saves --last 1000`
(the level is column 7, the campaign id column 6), for example
`awk 'NR>1 && ($7!="Legend" || $1 ~ /good/) {print $1}'`. Present the
deletions grouped by kind (geoscape, tactical mission chains), and name the
user-named saves that would go (such as `great`, `ok`, `autosave_1`) so they
can rescue them. Note whether the newest save survives.

A kind rule works the same way. "Clean up the in-mission saves except the
last one" means: keep every geoscape save of every campaign plus the newest
tactical save (the list is oldest first; kind is column 8), for example
`awk 'NR>1 && ($8!="tactical" || $1=="<newest tactical>") {print $1}'`.
When the user gives a rule like this and says the game is already at the
main menu, the request is the go-ahead: build the lists, check that the kept
and deleted counts add up to the save count and that no kept name is on the
delete list, delete, then report what went (including named saves) and ask
the user to quit the game so Steam Cloud syncs.

A count rule thins one campaign: "keep about 6 geoscape saves, including the
last, and only the most recent in-mission save". Keep every save of the other
campaigns. In the target campaign, keep the newest geoscape save (usually
`autosave`) plus picks spread over the in-game timeline, denser near the end,
for example one before and one after each big mission. Keep the newest
tactical save too. When two geoscape saves share an in-game day, keep the one
saved later in real time: it is the branch the user kept playing. Show a
table of the keepers (name, in-game date, real save time) and name every
user-named save that would go. If the user didn't say the game is at the
main menu and `pgrep` shows it running, ask before deleting: the newest
save may be the mission they are playing. Once they say go ahead, recheck
the plan, delete, and confirm the remaining saves match the keep list
exactly (`diff` of sorted names).

A request with no rule ("another round of cleanups for campaign X") means a
count rule on the current campaign: about 8 geoscape saves across the whole
campaign plus the newest tactical save. Keep only a few early keepers from
the last round and spend the rest on the stretch played since then, one
around each big mission. Propose the plan first and delete only on the
user's go-ahead. If the game is still running, their "go ahead" alone is
enough, but first check that no save is newer than the plan.

When the current campaign has just been won, a cleanup round thins it to
the run-up to the final mission: two or three geoscape saves from after the
last big mission, the newest geoscape save (usually `autosave`) and the
newest tactical save. Check with `ppach steam` that its achievement landed,
and keep the saves of campaigns that still have an ending to win.

A "full cleanup" covers every campaign at once. Finished campaigns go back
to the keepers of their last round (read them from the notes of that round);
campaigns with an ending still to win keep all their saves. The current
campaign keeps every geoscape save (it is mid-story, and its fork saves are
geoscape saves) plus the newest tactical save. Show the plan, then delete on
the user's "go ahead"; a permission check may block the delete until the
user has said it.

**Resurrected saves.** Pruned saves of a finished campaign can come back
weeks later: on disk with their original timestamps, local-only at first,
and in the cloud after the next exit. The likely source is a second Steam
client with its own copy of the save folder, such as a cloud-gaming session
(GeForce Now), which uploads its old saves when it syncs. This has not been
proven. When `ppach campaigns` shows a finished campaign with far more saves
than its last prune left, prune it again to the same keepers. Then tell the
user that a session on that other client may bring the saves back again.

Steam Cloud holds only the newest saves up to a size cap, so after a long
session older keepers drop out of the cloud. They are still safe on disk.
Report them as local-only, and offer to copy them to a backup folder outside
the synced save directory if the user wants a second copy.

Confirm each candidate with `ppach save` / `events`, write the keep list (one
save name per line) to the scratchpad, and show `ppach cloud --keep <file>`.
Then delete only after the user says so, in this order, because Steam Cloud
syncs this game only when the game starts and exits:

1. The user starts Phoenix Point and stays at the main menu. Check with
   `pgrep -il phoenix`.
2. Delete the files from `ppach cloud --keep <file> --paths` (recheck the
   plan first; the user may have saved since). Write the paths to a
   scratchpad file, check its count and that no kept name appears in it,
   then `while IFS= read -r f; do rm -- "$f"; done < delete.txt` (the
   paths contain spaces). Right after this, `ppach cloud` lists every
   deleted save as "in the cloud but not local"; that is expected until
   the game exits.
3. The user quits the game normally. Steam then removes the deleted saves
   from the cloud and uploads kept saves that were local-only.
4. Run `ppach cloud`: the file count should drop and nothing should be
   listed as not synced or missing locally. The cloud count is the save
   count plus a couple of non-save files. Steam itself can keep running;
   only the game has to quit. Have the user start the game
   once more to confirm deleted saves did not come back.

   If the user is already playing again when you check, judge success by
   the deleted saves alone: none of them in the cloud and none back on
   disk. Other differences are normal while the game runs. Saves made this
   session stay local until the game exits. The game can replace an autosave
   (for example `autosave_1` goes and `autosave` appears), which leaves the
   old one listed as "in the cloud but not local" until the next exit. Not
   every local-only keeper is uploaded on the first exit, either: some
   older saves have stayed local-only for no known reason. They are still
   safe on disk, so report them by name rather than treating them as a
   failure. A later clean exit can upload them: once, all 14 local-only
   keepers went up together, and the cloud then held every local save.
   `ppach cloud` showed "0 of them not in the cloud".

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
- Write the report the user sends to `~/phoenix-point-<topic>-bug.md`; it
  keeps their real setup. The copy added to `bug-reports/` here is for the
  public repository: replace the setup block with placeholders
  (`<version>`, `<OS and version>`, `<list from ppach version>`) and leave
  out dates and anything else that describes the user's own machine or play.
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

**Change the tool or this skill.** Both live in one **public** Git repository,
the one `install.sh` links from (`readlink ~/.claude/skills/phoenix-point-achievements`
shows where it is). Commit and push each change there. Before every commit:

- Keep the user's setup out of tracked files and commit messages: Steam and
  account ids, usernames and home paths, OS version, owned DLCs, play dates,
  campaign progress and local backup locations. The game's own def names,
  GUIDs and build number are fine.
- Run a search over the diff for those, plus the user's actual Steam id and
  account id (from the save directory name and `steam_autocloud.vdf`), and
  credential patterns. A clean working tree says nothing about the commit
  message, so check that too.
- Once something personal has been pushed to a public repository, a later
  rewrite does not retract it. Ask before pushing anything you are unsure of.

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
