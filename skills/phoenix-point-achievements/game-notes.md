# Phoenix Point achievement notes

Facts worked out from the game's definitions (`ppach def ...`) and from real
saves while finishing the achievement list. Game build 75137 (Steam, macOS).

## Where progress lives

- Achievements that span campaigns ("Master Manufacturer", "Master
  Scientist", "I Can Do Everything", "Class Creator", "All Possibilities"...)
  are tracked in `Options.jopt`, not in the saves. `ppach progress` diffs it
  against the lists the game checks.
- The game writes `Options.jopt` lazily, and Steam Cloud syncs it. Something
  you did a minute ago may not be there yet.
- Steam's local stats cache only holds counters, and they lag the game (for
  example "Master Scientist" counts to 117 on Steam but 126 in the game).

## Master Scientist: Project Vulture (New Jericho)

`NJ_ProjectVulture_ResearchDef` is only unlocked by the Harlson chain:

1. **CHAIN_NJ1 "Hecate's Children"** fires after researching Jack Harlson.
   Choice 0 sends you on a mission to the Byzantium site (an Exploration
   site you must visit); choice 1 sets `Harlson` directly.
2. A change in `Harlson` fires **CHAIN_NJ2 "Putting Bullets in Monsters"**.
   Choice 1 "Harlson is right." sets `Vulture`; choice 0 is a mission whose
   win sets it.
3. A change in `Vulture` fires **CHAIN_NJ3 "The Philosopher King"** (needs
   good New Jericho relations). Choice 0 **"Harlson is right. Whatever it
   takes."** unlocks Project Vulture. Choice 1 (Richter) locks it out for
   that campaign.

If you already chose Richter, reload a geoscape save from before CHAIN_NJ3:
`ppach events <save> --match CHAIN_NJ --text` shows where each save stands.

## Master Manufacturer: the three turret magazines

The list includes `NJ_TechTurretGun_AmmoClip_ItemDef` (Watcher AT Magazine),
`NJ_PRCRTechTurretGun_AmmoClip_ItemDef` (Rattlesnake AT Magazine) and
`PX_LaserTechTurretGun_AmmoClip_ItemDef` (Scorcher AT Magazine). They are
tagged as manufacturable, but in this build the UI never offers them: turrets
only show "+ITEM" (the turret itself), never "+AMMO". Building the turret
does not count. There is no known in-game way to get these three. An
example bug report for the developers is in
[bug-reports/master-manufacturer-turret-magazines.md](bug-reports/master-manufacturer-turret-magazines.md).
The developers no longer support the unmodded game, so the fix is editing
`Options.jopt` (players report the Terror from the Void mod handles this
achievement properly). The edit has been done and verified, with the game
closed and a backup first:

- Each list entry is a reference to its own object
  `{"ObjectID": n, "TopLevel": false, "ObjectValue": {"#Type": t,
  "SerializationGuid": g}}`, where `t` is the `Types` id of the def's C#
  class. The magazines share their script class with every other clip, which
  the file stores as `PhoenixPoint.Tactical.Entities.Equipments.TacticalItemDef`.
- Object ids are contiguous, so new objects take the next ids, appended to
  `Objects`, and one `{"ObjectID": n}` each goes on the list. `CreateOrder`
  lists types, not objects, and needs no change.
- The file is `json.dumps(indent=2)` byte for byte, so check a round trip
  before rewriting it, and confirm that the edit changes nothing else.
- **Result:** `ppach progress` showed 177/177 right after the edit, and the
  achievement unlocked at the next launch, during the intro video, with
  nothing else to do in-game. There was no Steam Cloud conflict: the edited
  file was uploaded at launch (its SHA-1 in `remotecache.vdf` matched).
- When the game next saved, it renumbered the objects into reference order
  (new ids 270-272 for the magazines). The resolved content was identical,
  so a byte diff against your edit is not evidence of a problem.
- The script is [fixes/master-manufacturer-add-magazines.py](fixes/master-manufacturer-add-magazines.py).
  It runs as a dry run unless given `--apply`, and refuses to run when the file
  differs from the backup's checksum or a magazine is already recorded.

## I Can Do Everything: Technician abilities

`ManualControl_AbilityDef` (Remote Control) only targets Phoenix-faction,
non-structural, metallic actors, so enemy turrets never qualify. Use it on
your own deployed turret or a Phoenix vehicle. Field Medic and Electric
Reinforcement are also Technician abilities in the list.

## All Possibilities: five endings

Required: `PXVictory`, `NJVictory`, `ANVictory`, `SYPolyVictory`,
`SYTerraVictory` (CustomMissionTypeDefs). One faction ending per campaign: a
faction ending needs that faction's story chain and a relation of 75+ with
it. The final mission is at the Pandoran Palace, which your own main
research has to reveal first, so that research chain sets the campaign's
length whichever faction you back.

### Synedrion: Polyphonic or Terraformation

The two Synedrion endings depend on the story variables `Polyphonic` and
`Terraformers`:

- **PROG_SY1** choice: +2 to one of them.
- **PROG_SY3_WIN "The Man Who Would Be Pirate King"**: choice 0 "Humanity
  matters most. Share with Terraformers." (+2 Terraformers); choice 1 "We
  must heal, not dominate. Share with Polyphonic Tendency." (+2 Polyphonic);
  choice 2 "We don't do Synedrion drama. Share with both." (no change).
- Random Synedrion events SY18, SY23, SY25 and SY29 add +1.
- With relation above 74, the ending is fixed when **PROG_SY6_P "Liberty or
  Death"** (Polyphonic > Terraformers) or **PROG_SY6_T "The Master's Tools"**
  (Terraformers >= Polyphonic; **a tie goes to Terraformation**) fires,
  after `Moon` = 1 (PROG_SY5 "Moonshot") and a research completion.

To get both endings, reload a geoscape save from before PROG_SY3_WIN that
has good Synedrion relations and play it twice. Find candidates with:

    ppach timeline --campaign <id> --rel 'SY>PX' --rel 'AN>SY' --var Polyphonic --var Terraformers

Watch for an Anu–Synedrion war (the `war` column): once it starts, Synedrion
havens can be wiped out quickly.

## Extreme Victory (Legend) and Under my Thumb

- Legend is the `VeryHard` difficulty; `ppach campaigns` labels it.
- Backing Anu worked well in practice: its story chain can be finished and
  the faction allied by about in-game March. Anu's Priests also give the
  mind-control route to **Under my Thumb** (control 3 enemies at once with
  one Priest).
- General advice (not from game data): ally with one faction early and stay
  friendly with the rest, push the research that reveals the Palace, keep a
  small, well-equipped squad, clear Pandoran nests early, defend bases, and
  keep named manual saves before big choices.
