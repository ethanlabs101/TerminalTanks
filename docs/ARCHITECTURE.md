# Architecture

Terminal Tanks is one Python package, `tanks`, started by `terminaltanks.py`. It uses the standard library only. This page
explains how the pieces fit; [ADDING_CONTENT.md](ADDING_CONTENT.md) has the recipes for extending the game.

## Start-up and the frame loop

```
terminaltanks.py ── tanks.app.main()
                      ├─ parse_cli()                       command-line options
                      ├─ TerminalIO (terminal.py)          raw keys in, ANSI out, terminal always restored on exit
                      └─ Application (app.py)
                           ├─ SaveData / ProfileBook       progress and profiles (save.py, profiles.py)
                           ├─ make_audio()                 helper process, Web Audio or silence (audio/clients.py)
                           └─ run(): 30 frames a second
                                step(dt): input ─> top scene ─> draw ─> Screen.flush()
```

The **Application** keeps a stack of scenes. `goto()` replaces the stack (with a fade), `push()` / `pop()` open and close
overlays such as the pause menu. Every frame it reads input, hands the events to the top scene, updates and draws the
stack, then flushes the screen. It also routes music (each scene says which song it wants), effects, the wallet chime and
the NOW PLAYING card.

## Layers

Modules import only from modules **below** them, so any module can be imported on its own and import order never
matters:

| Layer | Modules |
|---|---|
| foundation | `config`, `colors`, `terminal`, `screen`, `settings` |
| content (data) | `content/*`: maps, tanks, ammo, paints, home screens, shop, missions, tickets, tournament, rewards, story, songs, ... |
| drawing | `art/*` |
| simulation | `battle/*` |
| persistence | `save`, `profiles`, `net` |
| audio | `audio/*` |
| interface | `ui/*` |
| flow | `match/*` and `scenes/*` |
| application | `app`, `web` |

Screens open one another (the main menu opens nearly every screen, and most screens return to it), and a session decides
which screen follows a match. Where a module needs something defined above it, it imports it **inside the function that
uses it**; there are 13 such functions, all in `scenes/` and `match/`. `MenuScene.handle` is the largest, because the main
menu is the hub. Nothing else in the package has a circular import.

## Scenes

A scene (`scenes/base.py`) has five methods: `enter`, `exit`, `handle(event)`, `update(dt)` and `draw(screen)`.
`BackdropScene` adds the animated menu backdrop. Screens live in `scenes/`, one module per area (main menu, setup,
battle, shop, missions, tournament, jukebox, ...).

## Matches: sessions and the battle

A **session** (`match/sessions.py`, `match/martyr.py`) is one match from the first round to the result screen.
`MatchSession` is a plain match; `MissionSession`, `TicketSession`, `TournamentSession`, `PracticeSession` and
`MartyrSession` override its hooks:

| Hook | Decides |
|---|---|
| `song()` | the battle music |
| `on_turn_start`, `dmg_mult` | boss behaviour (ammo swaps, huge health pools) |
| `record_round`, `over`, `champion`, `completed`, `failed` | how rounds are won and when the match ends |
| `hud_title`, `hud_wins`, `banner_title`, `banner_note`, `round_summary` | what the HUD and the round results say |
| `interlude` | a scene between rounds (the Martyr's cutscenes) |
| `commit` | the payout and unlocks, written to the save |
| `finish_scene`, `exit_scene`, `restart` | where the game goes next |

**BattleScene** (`scenes/battle.py`) runs the turns of one round. It builds a **BattleWorld** (`battle/world.py`:
terrain, scenery, tanks, wind, particles and explosions), takes aim input or asks the **AI** (`battle/ai.py`, an aim
solver that learns from its misses), and fires. A shot is planned once, at fire time, by `plan_shot()`
(`battle/shots.py`) as a list of flights (arcs traced by `battle/physics.py`) that end in impact events; every ammo
mechanic (bounce, split, cluster, burrow, pierce, seek, chain, volley, ...) is built from those two pieces. The scene
then plays the flights back and applies each event: craters, damage and effects.

## Drawing

Everything is drawn into a **PixelCanvas** (two pixels per character cell, using half-block characters) or directly
into the **Screen** (`screen.py`), a grid of cells. `Screen.flush()` sends only the cells that changed: as ANSI escape
codes in a terminal, or as packed cell records to the browser page. `art/` holds all drawing code (tanks, shells,
scenery, home-screen layers, album covers, bosses); it reads content but holds no game rules.

## Content

`content/` is plain data plus small helper functions. The shop (`content/shop.py`) is built from the content lists: the
n-th tank, ammo, home screen or map of a list lands in price tier n // 15 (four tiers of 15, then premium). Unlock ids are
`"kind:key"` strings (`tank:scout`, `ammo:lob`, `map:mesa`, `theme:neon`, `paint:void`, ...) and are stored in save
files, so a key must never change once it has shipped.

## Audio

Nothing is sampled: every sound is synthesized.

```
audio/synth.py          oscillators, instruments, drum kits, filters
audio/composer.py       SongSpec ─> compose() ─> a Song: timed note events per stem
audio/notebank.py       the notes a song needs, rendered once (cached on disk)
content/songs.py        the hand-written soundtrack (SONGS)
audio/house_composer.py writes a song for every home screen and battlefield without a hand-written one
audio/director.py       which song plays where; what the Jukebox has unlocked
audio/mixer.py          real-time mixer: song players, stem moods, effects, ducking, EQ, analyser
audio/sfx.py            named effects, plus a fire and an impact sound generated for every ammo
audio/output.py         OS outputs, and the helper process (terminaltanks.py --audio-server)
audio/clients.py        AudioClient (talks to the helper), WebAudio (browser), NullAudio (silent)
```

On the desktop the mixer runs in a helper process started from `terminaltanks.py --audio-server`; the game sends it short
text commands, so audio work can never stall a frame. Generated songs are seeded from their own id, so adding content
never changes an existing song.

## Saves

`SaveData` (`save.py`) is written as JSON with a version number. Loading upgrades older versions; custom-tank records keep
fields from newer versions; each write goes to a temporary file that then replaces `save.json`. `ProfileBook`
(`profiles.py`) keeps up to three profiles; profile 1 is the original `save.json`.

## The browser version

The website runs this same code in Pyodide. It imports `terminaltanks.py` (which re-exports the functions in
`tanks/web.py`), calls `web_frames()` and steps the game once per animation tick; keys and the grid size come in through
`web_feed()` and `web_resize()`. `WebTerminalIO` hands the page cell records instead of ANSI text. The page loads the
`tanks/` files by following the imports, so no build step is needed.

## Tests

`tests/test_game.py` (standard library `unittest`) imports every module, checks content integrity (unique keys, shop
items and music that point at real content, paint sentinels), round-trips a save, walks the menus with random keys
and plays an AI-vs-AI battle to its result, all headless and in temporary folders.
