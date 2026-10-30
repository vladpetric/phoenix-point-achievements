Subject: "Master Manufacturer" can't be completed: three turret magazines can never be manufactured

Hi,

I'm going for all the achievements in Phoenix Point, and "Master Manufacturer"
("Manufacture an item of each type") seems to be impossible to finish. I'm
stuck at 174/177. The last three items on the achievement's list are turret
magazines that the game never lets me build.

The three missing items (internal def names, from the achievement's item
list `ManufactureAllItems_AchievementDef`):

- `NJ_TechTurretGun_AmmoClip_ItemDef` (Watcher AT magazine)
- `NJ_PRCRTechTurretGun_AmmoClip_ItemDef` (Rattlesnake AT magazine)
- `PX_LaserTechTurretGun_AmmoClip_ItemDef` (Scorcher AT magazine)

All three carry `ManufacturableItem_TagDef`, so they count toward the
achievement. But in the manufacturing screen the turrets only ever have the
"+ITEM" option (the turret itself), never "+AMMO", and the magazines are not
listed anywhere else. I have researched everything (Master Scientist is
unlocked, 126/126) and built the Watcher AT and Rattlesnake AT turrets
themselves, but building a turret does not count for its magazine.

Every other item on the list I have built across my campaigns, so these three
are the only thing standing between me and the achievement.

Steps to reproduce:
1. Research the New Jericho and Phoenix turret technologies.
2. Open Manufacturing and look at the Watcher AT, Rattlesnake AT and
   Scorcher AT turrets.
3. Only the turret can be queued. There is no way to manufacture its
   magazine, so the three items above never get recorded for the
   achievement.

Expected: either the magazines can be manufactured, or they are removed from
the "Master Manufacturer" list.

Setup:
- Phoenix Point <version> (build <build>), <store> version on <OS and version>
- DLCs owned: <list from `ppach version`>

If it helps, I can send my Options.jopt, which shows the 174 recorded items.

Thanks for the game, and for taking a look!
