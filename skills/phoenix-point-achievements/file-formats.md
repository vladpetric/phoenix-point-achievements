# Phoenix Point file formats

## Locations (macOS, Steam)

| What | Path |
|---|---|
| Saves and `Options.jopt` | `~/Library/Application Support/com.snapshotgames.phoenixpoint/Steam/<steam id>/` |
| Game definitions | `~/Library/Application Support/Steam/steamapps/common/Phoenix Point/PhoenixPointOSX.app/Contents/Resources/Data/sharedassets0.assets` |
| Steam stats cache | `~/Library/Application Support/Steam/appcache/stats/UserGameStats_<account>_839770.bin` and `UserGameStatsSchema_839770.bin` |
| Game log (version, owned DLCs) | `~/Library/Logs/Snapshot Games Inc/Phoenix Point/Player.log` (and `Player-prev.log`); the telemetry line has `app_version` and `BoughtDLCs` |
| Steam Cloud tracking | `~/Library/Application Support/Steam/userdata/<account id>/839770/remotecache.vdf`; the account id is in the save directory's `steam_autocloud.vdf` |

## Object graph (both `.jopt` and `.zsav`)

Objects live in `Contents.Objects` as `{"ObjectID": n, "ObjectValue": ...}`,
with one marked `TopLevel`. A value of `{"ObjectID": n}` is a reference.
Collections are `{"CollectionValues": [...]}`; dictionaries are collections
of `{"Key", "Value"}`. Scalars are often boxed as `{"BoxedValue": x}`. Keys
starting with `#` are type bookkeeping. Defs are referenced by
`{"SerializationGuid": "..."}`; `ppach` maps those GUIDs to def names.

`Options.jopt` is that graph as JSON. The `Achievement_*` keys hold the
cross-campaign progress (GUID lists, research names, class-pair codes such
as `"pr,te"`, or flags and counters).

## `.zsav`

Gzip of a tagged binary encoding of the same graph:

- 9 header bytes (`'O'` + 8), then top-level fields: `Version`, `Metadata`,
  `Geoscape`, `LevelParams`, `Contents`, `RuntimeDefs`.
- `0x0e <int32 id>` names a field via the field-name table.
- Value tags: `0x01` null, `0x02` bool, `0x03`–`0x05` byte, `0x06`/`0x07`
  int16/uint16, `0x08`/`0x09` int32/uint32, `0x0a`/`0x0b` int64/uint64,
  `0x0c` float, `0x0d` double.
- `0x0f <int32 total length> <7-bit length> <utf8>` string.
- `0x10 <int32 byte length> values...` list; `0x11 <int32 byte length>
  (field, value)...` object. The lengths make skipping cheap.
- The field-name table is a run of `0x0f` strings at the very end of the
  file, found by scanning backwards for a run that ends exactly at EOF.

`Metadata` holds the campaign id (`GameId`), in-game time, save time,
difficulty and whether it is a tactical (mission) save. Geoscape saves also
hold diplomacy (`_diplomacy` between `_thisParty`/`_withParty`), wars
(`AtWar`), story variables (`CustomVariables`), havens (`HavenData`,
`Population`, `OwnerFactionDef`) and the story log (`EncounterRecords`:
`EventId`, `_selectedChoice`, `FirstTriggerAt`). **Tactical saves carry none
of the geoscape state.**

Times are .NET ticks: 100 ns units since 0001-01-01.

## `sharedassets0.assets`

A Unity serialized file. Defs are MonoBehaviours whose name is a
length-prefixed string at byte 28 of the raw data. Achievement lists are
arrays of local PPtrs (`int32 file id = 0`, `int64 path id`); research is
stored as names. Localization entries are `"Category/KEY"`, padding, an
int32 language count, then one length-prefixed string per language with
English first. Event texts use keys such as `PROG_SY3_WIN_CHOICE_0_TEXT`.

### Reading a condition's operator

`ppach def` prints only a def's strings, so it hides the operator of a
variable comparison (`[<EVENT>] Condition <n>`). Never infer the operator
from which variable is listed first. In the raw bytes the condition holds
a variable name, a second variable name (an empty string when the variable
is compared with a number), an int32 value and an int32 operator. Strings
are int32-length-prefixed and padded to 4 bytes. So `[PROG_SY6_P] Condition
2` is `Polyphonic`, `Terraformers`, 0, 32 (Polyphonic >= Terraformers) and
`[PROG_SY6_P] Condition 3` is `Moon`, "", 1, 8 (Moon == 1). Dump them with
the cache venv:

    cd <repo> && ~/.cache/ppach/venv/bin/python -c '
    import sys; sys.path.insert(0, ".")
    from ppach import gamedata
    A = gamedata.Assets()
    b = A.raw(A.byname["[PROG_SY6_P] Condition 2"]); print(b.hex(" ", 4))'

The game's `ComparisonOperator` enum: None 0, Less 2, Greater 4, Equal 8,
LessOrEqual 16, GreaterOrEqual 32 (`DiplomacyOperator`: Greater 0, Less 1).
To re-read an enum after a game update, install `dnfile` into a scratch venv
(not the ppach one) and read the `Constant` rows of the enum's fields in
`PhoenixPointOSX.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll`.
The type names are `ComparisonOperator`, `VariableCompareOperator` and
`DiplomacyOperator`.

## Steam stats cache

Binary KeyValues. The schema maps each stat id to either a counter or a
bitfield of achievements; the user file holds the values.

## Steam Cloud (`remotecache.vdf`)

Text KeyValues: `ChangeNumber`, then one block per synced file (path under
`Snapshot Games Inc/Phoenix Point/Steam/<steam id>/`) with size, times, sha
and `syncstate` (1 = synced). Auto-Cloud syncs this game when it starts and
exits. The cloud held only the ~73 newest saves (about 155 MB), so older
saves can be local-only. Saves deleted while the game was running were
dropped from the cloud on exit, and local-only files were uploaded then.
The cap pushes older saves out: after one long session of about 45 new
saves, the cloud held only 25 files (about 155 MB), all from that session,
and every older keeper was local-only again. After a prune and exit, only
the newest few keepers came back to the cloud.
