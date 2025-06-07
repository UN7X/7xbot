import types
from pathlib import Path
import importlib.util
import pathlib

import pytest

spec = importlib.util.spec_from_file_location(
    "botmod", pathlib.Path(__file__).resolve().parents[1] / "7xbot.py"
)
botmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(botmod)


def test_days_until_christmas_range():
    days = botmod.days_until_christmas()
    assert 0 <= days <= 366


def test_get_uptime_non_empty():
    assert botmod.get_uptime()


def test_db_save_load(tmp_path: Path):
    data = {"a": 1}
    file = tmp_path / "db.json"
    botmod.save_db(data, filename=str(file))
    loaded = botmod.load_db(filename=str(file))
    assert loaded == data


def test_get_bot_info_keys():
    fake_bot = types.SimpleNamespace(latency=0.05)
    fake_ctx = types.SimpleNamespace(guild=types.SimpleNamespace(shard_id=2))
    info = botmod.get_bot_info(fake_bot, fake_ctx)
    assert set(info.keys()) == {"ping_ms", "shard_id", "cpu_load"}


