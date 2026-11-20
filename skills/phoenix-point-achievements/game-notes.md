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
has good Synedrion relations and play it twice. In a new campaign, pick
PROG_SY1 choice 0 "Mist Repellers could help humanity regain its balance."
(Polyphonic +2), then save just before PROG_SY3_WIN: sharing with the
Terraformers gives 2–2 (a tie, so Terraformation) and sharing with Polyphonic
gives 4–0. That one save forks the campaign into both endings. Check the
variables after the Terraformer branch, because a random +1 can break the
tie. The achievement def names no difficulty, so the easiest one works.
Find fork candidates in an existing campaign with:

    ppach timeline --campaign <id> --rel 'SY>PX' --rel 'AN>SY' --var Polyphonic --var Terraformers

Watch for an Anu–Synedrion war (the `war` column): once it starts, Synedrion
havens can be wiped out quickly. `AN>SY` drifts down early even with neutral
play, so track its trend at each check.

The chain between PROG_SY1 and Pirate King: PROG_SY7 (a Synedrion opinion
event), then PROG_SY2 "Seeking the Firebird", which triggers on a Synedrion
diplomacy change (`E_PROG_SY2_DiplomacyChanged`; the threshold is not in its
strings, and one run saw it fire with SY>PX between 27 and 45), then the
PROG_SY2 and PROG_SY3 missions, then PROG_SY3_WIN. PROG_SY1_WIN1 choice 0
("Even if it's challenging…") leaves both ending variables unchanged.

### Main story research to the final mission

The final mission opens with **PROG_PX "Knowledge is Power"**, which fires when
`PX_VirophageInjectorBomb_ResearchDef` (Virophage Injector) completes. That
event offers the faction final missions (PROG_PX_MISS, PROG_NJ5_MISS,
PROG_AN8_MISS, PROG_SY6_MISS1/2). The story missions that unlock the research,
in order:

1. `PX_PhoenixProject` research → PROG_PX10 "Whatever Happened to Dr. Symes?"
   (Symes retreat mission).
2. Symes-notes sites PROG_PX12 "Frozen", PROG_PX11 "Rise By Sin, By Virtue
   Fall" and the PROG_PX13 Cryolab mission "Cool Air" raise `PandoraVirus`;
   PROG_PX131 "Progress" unlocks `PX_Pandoravirus` research.
3. `PX_Pandoravirus` → PROG_PX132 "The Shadow of the Past" → PROG_PX14 time
   vault mission (WIN "The Shattered Sphere"), which unlocks Antediluvian
   Archaeology and the PROG_PX1 / PX15 missions.
4. PROG_PX1_WIN "What They Died For" (Antarctic) sets `Sphere`, which unlocks
   `PX_YuggothianEntity`.

Virophage Injector needs (from the ExistingResearchRequirementDefs):

- **Virophage Weapons** ← Pandoravirus + Pandoran Evolution (kill and capture
  evolved Pandorans).
- **Yuggothian Receptacle** ← Yuggothian Entity + Scylla Vivisection (Scylla
  Autopsy + Pandoran Capture and Containment ← Pandoran Colonies, then a live
  Scylla) + Pandoran Citadel (Pandoran Lair, which needs Colonies and
  destroying a Lair, then destroying a Citadel).
- **Pandoran Telepathic Nodule** ← Siren Vivisection ← Siren Autopsy (a dead
  Siren, then a live one).

Pandoran Colonies lists three reveal-site and three destroy-site
requirements; whether all are needed is unchecked. The slow parts are the
two live captures and the nest → Lair → Citadel assaults.

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
