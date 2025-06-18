import types
from pathlib import Path
import importlib.util
import pathlib

import pytest
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "botmod", ROOT / "7xbot.py"
)
botmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(botmod)


def test_days_until_christmas_range():
    days = botmod.days_until_christmas()
    assert 0 <= days <= 366


def test_get_uptime_non_empty():
    botmod.bot_start_time = botmod.datetime.now()
    assert botmod.get_uptime()


def test_db_save_load(tmp_path: Path):
    data = {"a": 1}
    file = tmp_path / "db.json"
    botmod.save_db(data, filename=str(file))
    loaded = botmod.load_db(filename=str(file))
    assert loaded == data


def test_load_db_missing_file(tmp_path: Path):
    file = tmp_path / "missing.json"
    loaded = botmod.load_db(filename=str(file))
    assert loaded == {}


def test_db_save_load_empty_dict(tmp_path: Path):
    data = {}
    file = tmp_path / "empty.json"
    botmod.save_db(data, filename=str(file))
    loaded = botmod.load_db(filename=str(file))
    assert loaded == data


def test_get_bot_info_keys():
    fake_bot = types.SimpleNamespace(latency=0.05)
    fake_ctx = types.SimpleNamespace(guild=types.SimpleNamespace(shard_id=2))
    info = botmod.get_bot_info(fake_bot, fake_ctx)
    assert set(info.keys()) == {"ping_ms", "shard_id", "cpu_load"}


def test_setup_wizard_success(monkeypatch):
    sends = []

    class FakeCtx:
        def __init__(self):
            self.author = object()
            self.channel = object()
            self._guild = types.SimpleNamespace(id=321, shard_id=1)

        async def send(self, content=None, embed=None):
            sends.append(content or embed)

        @property
        def guild(self):
            return self._guild

    ctx = FakeCtx()

    responses = iter([
        types.SimpleNamespace(content="none", author=ctx.author, channel=ctx.channel, role_mentions=[]),
        types.SimpleNamespace(content="yes", author=ctx.author, channel=ctx.channel, role_mentions=[]),
        types.SimpleNamespace(content="regular", author=ctx.author, channel=ctx.channel, role_mentions=[]),
    ])

    async def fake_wait_for(event, check=None, timeout=None):
        return next(responses)

    monkeypatch.setattr(botmod, "db", {})
    monkeypatch.setattr(botmod, "bot", types.SimpleNamespace(wait_for=fake_wait_for))
    saved = {}

    def fake_save_db(data):
        saved.update(data)

    monkeypatch.setattr(botmod, "save_db", fake_save_db)

    import asyncio
    asyncio.run(botmod.setup_wizard(ctx))

    assert saved["config"]["321"]["economy"] == "regular"


def test_setup_wizard_cancel(monkeypatch):
    sends = []

    class FakeCtx:
        def __init__(self):
            self.author = object()
            self.channel = object()
            self._guild = types.SimpleNamespace(id=654, shard_id=1)

        async def send(self, content=None, embed=None):
            sends.append(content or embed)

        @property
        def guild(self):
            return self._guild

    ctx = FakeCtx()

    responses = iter([
        types.SimpleNamespace(content="cancel", author=ctx.author, channel=ctx.channel, role_mentions=[])
    ])

    async def fake_wait_for(event, check=None, timeout=None):
        return next(responses)

    monkeypatch.setattr(botmod, "bot", types.SimpleNamespace(wait_for=fake_wait_for))
    monkeypatch.setattr(botmod, "db", {})
    monkeypatch.setattr(botmod, "save_db", lambda data: None)

    import asyncio
    asyncio.run(botmod.setup_wizard(ctx))

    assert any("cancelled" in str(msg).lower() for msg in sends)


def test_setup_wizard_help(monkeypatch):
    sends = []

    class FakeCtx:
        def __init__(self):
            self.author = object()
            self.channel = object()
            self._guild = types.SimpleNamespace(id=111, shard_id=1)

        async def send(self, content=None, embed=None):
            sends.append(content or embed)

        @property
        def guild(self):
            return self._guild

    ctx = FakeCtx()

    import asyncio
    asyncio.run(botmod.setup_wizard(ctx, args="help"))

    assert any(hasattr(msg, "title") and "Setup Command Help" in msg.title for msg in sends)


def test_get_shop_items():
    botmod.db = {"config": {"42": {"economy": "prankful"}}}
    items = botmod.get_shop_items_for_guild(42)
    assert "spam_ping" in items


def test_man_command_list(monkeypatch):
    sends = []

    async def fake_send(content=None, embed=None):
        sends.append(content or embed)

    ctx = types.SimpleNamespace(send=fake_send)

    monkeypatch.setattr(botmod, "man_pages", {"a": "b", "c": "d"})

    import asyncio
    asyncio.run(botmod.man_command(ctx, arg="--list"))

    assert "a" in sends[0]



def test_get_shop_items_regular():
    botmod.db = {"config": {"1": {"economy": "regular"}}}
    items = botmod.get_shop_items_for_guild(1)
    assert "vip" in items


def test_update_points():
    botmod.db = {}
    botmod.update_points("99", 10)
    assert botmod.check_points("99") == 10
    botmod.update_points("99", -3)
    assert botmod.check_points("99") == 7


def test_man_command_unknown(monkeypatch):
    sends = []
    async def fake_send(content=None, embed=None):
        sends.append(content or embed)
    ctx = types.SimpleNamespace(send=fake_send)
    monkeypatch.setattr(botmod, "man_pages", {"a": "b"})
    import asyncio
    asyncio.run(botmod.man_command(ctx, arg="zzz"))
    assert "No manual entry" in sends[0]


def test_beta_info_embed():
    sends = []

    class FakeCtx:
        def __init__(self):
            self.guild = types.SimpleNamespace(shard_id=1)
        async def send(self, content=None, embed=None):
            sends.append(embed)

    fake_bot = types.SimpleNamespace(latency=0.05)
    cog = botmod.Core(fake_bot)
    import asyncio
    asyncio.run(botmod.Core.beta.callback(cog, FakeCtx(), "info"))

    assert isinstance(sends[0], botmod.discord.Embed)
    field_names = [f.name for f in sends[0].fields]
    assert "Build" in field_names and "Uptime" in field_names
