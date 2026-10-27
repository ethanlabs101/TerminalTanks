"""Tests for Terminal Tanks. Standard library only:   python3 -m unittest discover -s tests

Every test runs headless (the web terminal backend, no audio) and only ever touches temporary save files."""
import importlib
import json
import os
import pkgutil
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["TT_NOAUDIO"] = "1"
os.environ.pop("TERMINALTANKS_SAVE", None)

import tanks  # noqa: E402
from tanks.app import Application  # noqa: E402
from tanks.audio.director import HOME_SONG, MAP_SONG, MARTYR_SONGS, TOURNAMENT_SONGS  # noqa: E402
from tanks.colors import ColorMode  # noqa: E402
from tanks.content.ammo import ALL_AMMOS, AMMO_BY_KEY  # noqa: E402
from tanks.content.homes import HOME_ORDER, HOME_THEMES  # noqa: E402
from tanks.content.maps import all_maps  # noqa: E402
from tanks.content.paints import ANIMATED_PAINTS, COLOR_CHOICES  # noqa: E402
from tanks.content.shop import SHOP_BY_UID, SHOP_ITEMS  # noqa: E402
from tanks.content.songs import SONGS  # noqa: E402
from tanks.content.tanks import ALL_DESIGNS, DESIGN_BY_KEY  # noqa: E402
from tanks.content.unlockables import unlockables  # noqa: E402
from tanks.match.sessions import MatchConfig, MatchSession, PlayerSetup  # noqa: E402
from tanks.save import SaveData  # noqa: E402
from tanks.scenes.battle import BattleScene  # noqa: E402
from tanks.scenes.rounds import RoundResultScene  # noqa: E402
from tanks.scenes.title import BootScene  # noqa: E402
from tanks.settings import Difficulty  # noqa: E402
from tanks.terminal import WebTerminalIO  # noqa: E402

FRAME = 1 / 30


def headless_app(save_path: Path, seed: int = 1, size=(110, 32)) -> tuple:
    """An Application on the web terminal backend, sized and on the boot screen. Returns (app, terminal)."""
    term = WebTerminalIO(lambda *frame: None, None, size)
    term.start()
    app = Application(term, seed, ColorMode.TRUE, save_path)
    app._swap(BootScene(app))
    app.step(FRAME)
    return app, term


class Modules(unittest.TestCase):
    def test_every_module_imports(self):
        names = [m.name for m in pkgutil.walk_packages(tanks.__path__, "tanks.")]
        self.assertGreater(len(names), 60)
        for name in names:
            importlib.import_module(name)

    def test_entry_script_reports_version(self):
        out = subprocess.run([sys.executable, str(ROOT / "terminaltanks.py"), "--version"], capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn(tanks.__version__, out.stdout)


class Content(unittest.TestCase):
    def test_keys_are_unique(self):
        for items in (ALL_DESIGNS, ALL_AMMOS, list(all_maps().values())):
            keys = [i.key for i in items]
            self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(SHOP_ITEMS), len(SHOP_BY_UID))

    def test_shop_items_point_at_real_content(self):
        maps = all_maps()
        for item in SHOP_ITEMS:
            kind, _, key = item.uid.partition(":")
            if kind == "tank":
                self.assertIn(key, DESIGN_BY_KEY)
            elif kind == "ammo":
                self.assertIn(key, AMMO_BY_KEY)
            elif kind == "map":
                self.assertIn(key, maps)
            elif kind == "theme":
                self.assertIn(key.upper(), HOME_THEMES)

    def test_every_unlockable_is_unique(self):
        uids = [u.uid for u in unlockables()]
        self.assertEqual(len(uids), len(set(uids)))

    def test_every_home_screen_and_battlefield_has_music(self):
        for key in HOME_ORDER:
            self.assertIn(HOME_SONG[key], SONGS, key)
        for key in all_maps():
            self.assertIn(MAP_SONG[key], SONGS, key)
        for sid in TOURNAMENT_SONGS + MARTYR_SONGS:
            self.assertIn(sid, SONGS)

    def test_home_screen_mascots_exist(self):
        for theme in HOME_THEMES.values():
            self.assertIn(theme.hero, DESIGN_BY_KEY, theme.key)
            self.assertIn(theme.hero_ammo, AMMO_BY_KEY, theme.key)

    def test_paint_sentinels_never_clash_with_real_colours(self):
        sentinels = [p.sentinel for p in ANIMATED_PAINTS]
        self.assertEqual(len(sentinels), len(set(sentinels)))
        self.assertFalse(set(sentinels) & {c for _, c in COLOR_CHOICES})


class Saves(unittest.TestCase):
    def test_round_trip_keeps_progress(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "save.json"
            sv = SaveData(path)
            sv.complete_level(1)
            sv.complete_mission(1)
            sv.coins, sv.credits, sv.playtime = 1234, 56, 78.9
            sv.grant("tank:" + ALL_DESIGNS[30].key)
            sv.story = {"first_battle"}
            sv.flush()
            again = SaveData.load(path)
            self.assertEqual((again.coins, again.credits, again.playtime), (1234, 56, 78.9))
            self.assertIn(1, again.completed)
            self.assertIn(1, again.mission_completed)
            self.assertTrue(again.is_unlocked("tank:" + ALL_DESIGNS[30].key))
            self.assertEqual(again.story, {"first_battle"})
            self.assertEqual(json.loads(path.read_text())["version"], SaveData.VERSION)

    def test_unreadable_save_starts_fresh_without_touching_the_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "save.json"
            path.write_text("this is { not json")
            sv = SaveData.load(path)
            self.assertEqual(sv.coins, 0)
            self.assertEqual(path.read_text(), "this is { not json")


class Play(unittest.TestCase):
    def test_menus_survive_a_long_random_walk(self):
        keys = ["\x1b[A", "\x1b[B", "\x1b[C", "\x1b[D", "\r", " ", "\x1b"]
        rng = random.Random(7)
        with tempfile.TemporaryDirectory() as td:
            app, term = headless_app(Path(td) / "save.json")
            for frame in range(3000):
                if frame % 6 == 0:
                    term.push_keys(rng.choice(keys))
                if not app.running:
                    app, term = headless_app(Path(td) / "save.json")
                app.step(FRAME)

    def test_an_ai_battle_reaches_a_result(self):
        with tempfile.TemporaryDirectory() as td:
            app, _ = headless_app(Path(td) / "save.json", seed=3)
            ai = lambda name, team, colour: PlayerSetup(name, "CPU", colour, (255, 255, 255), True, "ranger", "standard", 3, team=team,
                                                         diff=Difficulty.MASTER)
            cfg = MatchConfig([ai("LEFT", 0, (90, 230, 255)), ai("RIGHT", 1, (255, 120, 90))], False, Difficulty.MASTER, "single")
            app.goto(BattleScene(app, MatchSession(cfg, None, 11)), fade=False)
            for _ in range(30 * 60 * 5):
                app.step(FRAME)
                if any(isinstance(s, RoundResultScene) for s in app.stack):
                    break
            self.assertTrue(any(isinstance(s, RoundResultScene) for s in app.stack), "no round result within five game minutes")


if __name__ == "__main__":
    unittest.main()
