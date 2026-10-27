# Adding content

Almost everything in Terminal Tanks is a row in a table under `tanks/content/`. Add a row and the game picks it up
everywhere: the shop lists it, the unlock rules know it, it gets music and sound, and the website's catalog tools can
read it. After any change, run the tests:

```sh
python3 -m unittest discover -s tests
```

## Three rules that keep saves safe

1. **Never rename or remove a key** that has shipped (`"scout"`, `"lob"`, `"MEADOW"`, a map's name...). Saves store
   unlocks as `"kind:key"`, so a renamed key silently takes the item away from players. Display names and blurbs can
   change freely; a map's key comes from its name (`"MESA"` -> `mesa`), so keep a shipped map's name.
2. **Add new shop items at the end of their list.** A shop page is priced by position: the first 15 items are tier 1,
   the next 15 tier 2, and so on for four tiers; everything after that is premium (gold coins and credits). Adding to the
   end of the premium group never moves an existing item to another tier or price.
3. **Add new maps and home screens at the end too.** The music director hands out the hand-written battle themes in list
   order, so adding at the end leaves every existing battlefield on its current song.

## A tank

Tanks live in `tanks/content/tanks.py`. A design is an 11 x 6 pixel mask built from a turret, a hull and a track
(two rows each). Add a row to `_PREMIUM_TANKS` (the end of the shop's TANKS page):

```python
    _N("rivet", "RIVET", "A riveted brute on heavy treads.", "box/armor/heavy", "howitzer", "pulse", "smoke+sparks",
       (190, 200, 210)),
```

| Field | Value |
|---|---|
| key | unique, lowercase; the unlock id becomes `tank:rivet` |
| name, blurb | shown in the shop, setup and catalog |
| parts | `"turret/hull/track"`: keys of `TURRETS`, `HULLS`, `TRACKS` in the same file |
| barrel | a key of `BARRELS` (`tanks/art/barrels.py`): `single`, `twin`, `howitzer`, `crystal`, ... |
| glow | a key of `GLOW_STYLES` (`tanks/art/tanks.py`): how `l` pixels animate (`none`, `pulse`, `flame`, `prism`, ...) |
| ambient | keys of `AMBIENT_KINDS` (`tanks/art/tanks.py`) joined with `+`: `"fire+smoke"`, `"orbit+sparkle"`, or `"none"` |
| accent | RGB of the accent (`a`) pixels |
| options | an optional dict: `{"paint": (r, g, b)}` gives the tank its own colour whatever hull colour is picked; `{"hover": 2.0}` makes it float |

That's all: it appears in the shop with a premium price, and owning it puts it in the setup screen.

**New parts.** Add to `TURRETS`, `HULLS` or `TRACKS` (two strings of 11 characters each). The letters are colours:
`t` turret, `h` hull, `g` hull highlight, `k` and `w` tracks and wheels, `d` dark detail, `a` accent, `l` glowing pixels,
`.` empty. Every other letter is a material (`tanks/art/materials.py`): `p`/`q` crystal, `f`/`e` fire, `v` void, `b`
storm, `y` gold, and more. A part named in `PREMIUM_PARTS` is offered in the Workshop only to players who own a tank
that uses it.

## An ammo

Ammo lives in `tanks/content/ammo.py`. Add a row to `_PREMIUM_AMMOS`:

```python
    _A("hopscotch", "HOPSCOTCH", "Skims the ground twice before it blows.", "orb", "glow", "ring", (("bounce", 2), ("radius", 1.1))),
```

| Field | Value |
|---|---|
| key, name, blurb | as for tanks; the unlock id becomes `ammo:hopscotch` |
| proj, trail, boom | the shell, tracer and blast looks. Reuse any name already in the file (`orb`, `flame`, `comet`, ... / `glow`, `fire`, ... / `ring`, `nova`, `implode`, ...). A new look needs drawing code: shells in `tanks/art/projectiles.py`, trails and blasts in `tanks/battle/effects.py` |
| mechanics | `(key, value)` pairs, or `()` for a plain shell. Copy them from an ammo that behaves like what you want and tune the numbers; every key (`g`, `wind`, `speed`, `radius`, `dmg`, `bounce`, `cluster`, `apex`, `chain`, `burrow`, `pierce`, `seek`, ...) is handled in `plan_shot()` in `tanks/battle/shots.py` |

Its fire and impact sounds are generated from the proj and boom families and seeded by the key, so a new ammo always
sounds like itself.

## A battlefield

Maps live in `tanks/content/maps.py`. Add an entry to `_PREMIUM_MAPS`:

```python
    _M(3, "CHALK CLIFFS", "White cliffs above a cracked chalk plain.",
       [(0, .3), (.3, .3), (.4, .45), (.45, .2), (.5, .3)], "steppe", False, 0.02, (0.08, 0.92), "motes"),
```

`_M(tier, NAME, description, half_profile, theme, smooth, roughness, spawns, fx, aurora, buildings)`:

- **half_profile**: points `(x, height)` for the left half of the field, x from 0 to 0.5 and height from 0 (bottom) to
  1 (top); the right half is mirrored.
- **theme**: a name from `_THEMES` (`valley`, `alpine`, `arctic`, `volcano`, `moon`, `cyber`, ...) or a full
  `Theme(...)` (sky, far ridge, orb, ground colours, star density).
- **fx**: drifting particles, a key of `MOTE_STYLES` in `tanks/art/scenery.py` (`embers`, `snow`, `stardust`, `rain`,
  `sakura`, ...), or `"storm"`.
- **buildings**: an optional skyline baked into the sky (`skyline`, `temple`, `pyramids`, `castle`, `pagoda`, `kelp`,
  `torii`, `kaiju`, ...: see `_bake_buildings` in `tanks/art/scenery.py`).

The key is the name in lowercase with dashes (`chalk-cliffs`, unlock id `map:chalk-cliffs`). The music director writes the
battlefield its own song from its name and description; to pick a hand-written song instead, add the map key to
`_PREMIUM_MAP_SONGS` in `tanks/audio/director.py`.

## A home screen

Home screens live in `tanks/content/homes.py`.

1. Add a `HomeTheme` to `HOME_THEMES`. `_hx()` is the compact form:

   ```python
       _hx("CHALKCLIFFS", "CHALK CLIFFS", "Gulls over white cliffs.",
           ((255, 245, 225), (230, 210, 190), (120, 110, 150), (20, 18, 40)),   # sky, horizon -> zenith
           (150, 140, 160), (60, 56, 70), (255, 220, 160),                      # far ridge, ground, accent
           "motes", "rivet", "hopscotch", ("sun", "isles")),                   # particles, mascot tank + ammo, layers
   ```

   The mascot tank and ammo are drawn firing on the title screen; `layers` are scenery layers from `LAYER_DRAWERS` in
   `tanks/art/home_layers.py` (`moon`, `sun`, `city`, `mountains`, `grid`, `planet`, `pyramids`, `trees`, `rain`,
   `worldtree`, `whale`, ...), drawn back to front.
2. Add its key to the end of `SHOP_THEMES` (at the top of the same file) to sell it in the shop. A check at the bottom
   of the file makes sure every home screen is listed exactly once.

It gets its own generated song automatically. To use a hand-written one, map the key to a song id in `_HOME_HAND` in
`tanks/audio/director.py`.

**A new scenery layer** is one function in `tanks/art/home_layers.py`, `def _L_name(self, screen, cols, rows, t)`, that
paints onto the screen behind the menu (`self.th` is the HomeTheme, `t` the time in seconds), plus an entry in
`LAYER_DRAWERS`.

## A song

Hand-written songs live in `tanks/content/songs.py`:

```python
_S("chalk_wind", "CHALK WIND", "battle", 118, 45, "dor", "44", "desert",
   {"A": "1m 7M 6M 7M", "B": "4m 5m 1m 1m"},
   {"A": "1:4 3:4 5:4 4:2 3:2 | 2:8 r:8 | 1:4 3:4 5:4 7:4 | 1':16",
    "B": "4:4 5:4 6:8 | 5:4 4:4 3:8 | 2:4 3:4 4:4 5:4 | 1:16"}, desc="Wind along the cliffs.")
```

`_S(id, NAME, category, bpm, root_midi_note, scale, meter, style, progressions, melodies, form, desc, **options)`:

- **category**: `menu`, `battle` or `story` (its Jukebox shelf)
- **scale**: `maj`, `min`, `dor`, `phr`, `lyd`, `mix`, `hmin`, `phd`, `hung`, `pent`, `mpent`, `wt`, `loc`, `insen`
- **meter**: `44`, `34`, `68`, `78`, `54`, `58`, `98`, `128`
- **style**: an arrangement from `STYLES` in `tanks/audio/composer.py` (`ambient`, `synthwave`, `jig`, `waltz`, `metal`,
  `dnb`, `hymn`, ...)
- **progressions**: chords per section, as scale degrees (`1m`, `7M`, `4`, ...)
- **melodies**: `degree:length` notes in 16ths, `r` for a rest, `'` an octave up, `,` an octave down, `|` between bars
- **form**: the section order (default `"I A B A2 C X O"`)

Then give it a place to play: `_HOME_HAND` (a home screen) or `_PREMIUM_MAP_SONGS` (a battlefield) in
`tanks/audio/director.py`. It appears in the Jukebox once the player has heard it or unlocked where it plays.
`python3 terminaltanks.py --export-music out --only chalk_wind` renders it to a WAV file to listen to.

## A paint

Animated paints live in `tanks/content/paints.py`.

1. Pick a **sentinel**: an unused RGB colour such as `(242, 9, 241)`. It is never drawn as itself; it stands for the
   paint wherever a colour is stored. A check in the file rejects duplicates.
2. Write a **tint** `def chalk_tint(t) -> RGB` (its colour at time t: shells, trails, swatches) and, for a hull painted
   pixel by pixel, a **px** function `def chalk_px(t, c, r) -> RGB` (column and row on the hull).
3. Add it to `ANIMATED_PAINTS`: `AnimatedPaint("CHALK", CHALK, chalk_tint, chalk_px)`.
4. Sell it in `tanks/content/shop.py`: add `items.append(ShopItem("paint:chalk", 4, 4, "CHALK PAINT", "...", coins, credits))`
   next to the other paints in `_build_shop()`.

## Shop extras, cheats and unlocks

- **Shop extras** (page 4) are listed by hand at the end of `_build_shop()` in `tanks/content/shop.py`.
- **Cheat codes**: add `add(Cheat("mycode", ("tank:rivet",), text="RIVET UNLOCKED"))` in `_register_cheats()`
  in `tanks/content/cheats.py`. Cheats grant unlocks; they never add coins.
- **Unlockables**: anything with a new kind of unlock id must also be registered in `tanks/content/unlockables.py`, so
  that the unlock-everything cheat and the progress counters know it.

## Fixed-size content

The 20 Tournament levels, the 50 missions and the ten Terminal Ticket bosses are part of the story and the progression
rules (acts, gates, rewards), so their counts are checked when the game starts. Their numbers (bosses, health, prices,
rewards) can be tuned freely in `tanks/content/tournament.py`, `missions.py`, `tickets.py`, `martyr.py` and `rewards.py`.
