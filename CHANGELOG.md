# Changelog

## 2.0.0 (2026-10-26)

### Balance
- **UFO missions**: saucer health climbs from 8 on the first hunt (mission 3) to 24 on the last (mission 48); it used to
  start at 5 and grow by about one per hunt. Co-op saucers on missions 34, 39, 44 and 49 have 24, 30, 40 and 45 health
  (were 10, 15, 20 and 25).
- **The Mothership** has 30 health (was 24).
- **The Martyr**:

  | Phase | His health | Your health | His hits |
  |---|---|---|---|
  | I | 340 (was 250) | 175 | ×8 (was ×4) |
  | II | 525 (was 200) | 175 | ×5 |
  | III | 550 (was 260) | 200 (was 175) | ×6 |

  After a lost phase, the round summary suggests special ammo and Armageddon from the shop.
- Mission 49 is now called BROTHERS IN ARMS, so no two co-op missions share a name.

### Interface
- The shop's item panel no longer repeats your balance; your coins and credits stay in the top-right corner.
- The title screen tagline reads "pure Python, zero dependencies".
- Rock-paper-scissors says "YOU WIN!" (it said "YOU WINS!").
- The LINKS screen points at the real website and its repo (terminaltanks-site).
- The main menu shows the full-size TERMINAL TANKS logo whenever the whole menu fits under it (38 rows or more); it
  used to need 42 rows and fell back to the small "T A N K S" line on most screens.
- The thin strip of terminal that could show along the right and bottom edges is gone: the game colours the window's
  margin to match the screen and gives your terminal its own background colour back when it quits. Terminals that
  cannot report their colour are left untouched.

### Code
- The game is now the `tanks` package (81 modules in `content/`, `art/`, `battle/`, `match/`, `audio/`, `ui/` and
  `scenes/`), started by `terminaltanks.py`. It plays exactly as before: the same frames, sounds, battles and saves in a
  side-by-side comparison with the single-file version.
- Animated paints are one registry (`ANIMATED_PAINTS`); the colour pickers, hull painter, battle code and unlocks all
  read it.
- Each session type now names its own battle music (`song()`).
- Content checks guard what matters (unique keys, full shop tiers) instead of fixed item counts, so new tanks, ammo and
  maps can be added at the end of their lists.
- Unused code removed.
- New: automated tests (`tests/`), a player's guide ([docs/PLAYING.md](docs/PLAYING.md)),
  [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/ADDING_CONTENT.md](docs/ADDING_CONTENT.md).

## 1.6.0

The release before the package split: Tournament, Missions, Terminal Tickets, the Martyr, the shop, the Workshop, the
Jukebox, LAN play and save profiles.
