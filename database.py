import asyncpg
import asyncio
from typing import Optional, List, Dict, Any
import json
import os
from datetime import datetime

from urllib.parse import urlparse

class Database:
    def __init__(self, json_file: str = "database.json"):
        self.pool = None
        self.connection_url = os.getenv("DATABASE_URL")
        self.json_file = json_file
        self.use_json = False
        self.data: Dict[str, Any] = {}

        # Handle Heroku's updated DATABASE_URL format if needed
        if self.connection_url and self.connection_url.startswith("postgres://"):
            self.connection_url = self.connection_url.replace(
                "postgres://", "postgresql://", 1
            )
        if not self.connection_url:
            # Fall back to simple JSON storage
            self.use_json = True

    def _save_json(self) -> None:
        if not self.use_json:
            return
        with open(self.json_file, "w") as f:
            json.dump(self.data, f, indent=2)

    async def setup(self):
        """Initialize database and create tables"""
        if self.use_json:
            # Load JSON database from disk
            if os.path.exists(self.json_file):
                try:
                    with open(self.json_file, "r") as f:
                        first = f.read(1)
                        if first:
                            f.seek(0)
                            self.data = json.load(f)
                except json.JSONDecodeError:
                    self.data = {}
            return

        self.pool = await asyncpg.create_pool(self.connection_url)

        # Guild settings
        await self.pool.execute(
            """
            CREATE TABLE IF NOT EXISTS guilds (
                id BIGINT PRIMARY KEY,
                prefix TEXT DEFAULT '!',
                welcome_channel BIGINT,
                log_channel BIGINT,
                automod_enabled BOOLEAN DEFAULT FALSE,
                settings JSONB DEFAULT '{}'::jsonb
            )
            """
        )
        
        # User economy
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS economy (
                user_id BIGINT,
                guild_id BIGINT,
                balance BIGINT DEFAULT 0,
                bank BIGINT DEFAULT 0,
                daily_last TIMESTAMP,
                work_last TIMESTAMP,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        
        # User levels
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS levels (
                user_id BIGINT,
                guild_id BIGINT,
                xp BIGINT DEFAULT 0,
                level INTEGER DEFAULT 0,
                last_message TIMESTAMP,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        
        # Moderation logs
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS mod_logs (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT,
                user_id BIGINT,
                moderator_id BIGINT,
                action TEXT,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Warnings
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT,
                user_id BIGINT,
                moderator_id BIGINT,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    async def get_guild_prefix(self, guild_id: int) -> Optional[str]:
        """Get guild's custom prefix"""
        if self.use_json:
            guilds = self.data.get("guilds", {})
            return guilds.get(str(guild_id), {}).get("prefix")

        result = await self.pool.fetchrow(
            "SELECT prefix FROM guilds WHERE id = $1",
            guild_id,
        )
        return result["prefix"] if result else None
    
    async def set_guild_prefix(self, guild_id: int, prefix: str):
        """Set guild's custom prefix"""
        if self.use_json:
            guilds = self.data.setdefault("guilds", {})
            cfg = guilds.setdefault(str(guild_id), {})
            cfg["prefix"] = prefix
            self._save_json()
            return

        await self.pool.execute(
            """
            INSERT INTO guilds (id, prefix)
            VALUES ($1, $2)
            ON CONFLICT (id) DO UPDATE SET prefix = $2
            """,
            guild_id,
            prefix,
        )
    
    async def setup_guild(self, guild_id: int):
        """Setup a new guild in database"""
        if self.use_json:
            guilds = self.data.setdefault("guilds", {})
            guilds.setdefault(str(guild_id), {"prefix": "!"})
            self._save_json()
            return

        await self.pool.execute(
            """
            INSERT INTO guilds (id)
            VALUES ($1)
            ON CONFLICT (id) DO NOTHING
            """,
            guild_id,
        )
    
    async def get_balance(self, user_id: int, guild_id: int) -> Dict[str, int]:
        """Get user's economy balance"""
        if self.use_json:
            eco_guild = self.data.setdefault("economy", {}).setdefault(str(guild_id), {})
            user = eco_guild.get(str(user_id), {"balance": 0, "bank": 0})
            return {"balance": user.get("balance", 0), "bank": user.get("bank", 0)}

        result = await self.pool.fetchrow(
            "SELECT balance, bank FROM economy WHERE user_id = $1 AND guild_id = $2",
            user_id,
            guild_id,
        )
        if result:
            return {"balance": result["balance"], "bank": result["bank"]}
        return {"balance": 0, "bank": 0}
    
    async def update_balance(self, user_id: int, guild_id: int, amount: int):
        """Update user's balance"""
        if self.use_json:
            eco_guild = self.data.setdefault("economy", {}).setdefault(str(guild_id), {})
            user = eco_guild.setdefault(str(user_id), {"balance": 0, "bank": 0})
            user["balance"] = user.get("balance", 0) + amount
            self._save_json()
            return

        await self.pool.execute(
            """
            INSERT INTO economy (user_id, guild_id, balance, bank)
            VALUES ($1, $2, $3, 0)
            ON CONFLICT (user_id, guild_id) DO UPDATE
            SET balance = economy.balance + $3
        """,
            user_id,
            guild_id,
            amount,
        )
    
    async def get_user_level(self, user_id: int, guild_id: int) -> Dict[str, int]:
        """Get user's level and XP"""
        if self.use_json:
            lvl_guild = self.data.setdefault("levels", {}).setdefault(str(guild_id), {})
            user = lvl_guild.get(str(user_id), {"xp": 0, "level": 0})
            return {"xp": user.get("xp", 0), "level": user.get("level", 0)}

        result = await self.pool.fetchrow(
            "SELECT xp, level FROM levels WHERE user_id = $1 AND guild_id = $2",
            user_id,
            guild_id,
        )
        if result:
            return {"xp": result["xp"], "level": result["level"]}
        return {"xp": 0, "level": 0}
    
    async def add_xp(self, user_id: int, guild_id: int, xp: int) -> bool:
        """Add XP to user and return True if leveled up"""
        current = await self.get_user_level(user_id, guild_id)
        new_xp = current["xp"] + xp
        new_level = int(new_xp ** (1 / 4))

        if self.use_json:
            lvl_guild = self.data.setdefault("levels", {}).setdefault(str(guild_id), {})
            user = lvl_guild.setdefault(str(user_id), {"xp": 0, "level": 0})
            user["xp"] = new_xp
            user["level"] = new_level
            user["last_message"] = datetime.utcnow().isoformat()
            self._save_json()
        else:
            await self.pool.execute(
                """
                INSERT INTO levels (user_id, guild_id, xp, level, last_message)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, guild_id) DO UPDATE
                SET xp = $3, level = $4, last_message = CURRENT_TIMESTAMP
                """,
                user_id,
                guild_id,
                new_xp,
                new_level,
            )

        return new_level > current["level"]
    
    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str):
        """Add a warning to user"""
        if self.use_json:
            warn_guild = self.data.setdefault("warnings", {}).setdefault(str(guild_id), {}).setdefault(str(user_id), [])
            warn_id = len(warn_guild) + 1
            warn_guild.append({
                "id": warn_id,
                "moderator_id": moderator_id,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            })
            self._save_json()
            return

        await self.pool.execute(
            """
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
            VALUES ($1, $2, $3, $4)
            """,
            guild_id,
            user_id,
            moderator_id,
            reason,
        )
    
    async def get_warnings(self, guild_id: int, user_id: int) -> List[Dict]:
        """Get user's warnings"""
        if self.use_json:
            warn_guild = (
                self.data.setdefault("warnings", {})
                .setdefault(str(guild_id), {})
                .get(str(user_id), [])
            )
            return warn_guild

        results = await self.pool.fetch(
            """
            SELECT id, moderator_id, reason, timestamp FROM warnings
            WHERE guild_id = $1 AND user_id = $2
            ORDER BY timestamp DESC
            """,
            guild_id,
            user_id,
        )

        return [
            {
                "id": row["id"],
                "moderator_id": row["moderator_id"],
                "reason": row["reason"],
                "timestamp": row["timestamp"],
            }
            for row in results
        ]
    
    async def close(self):
        """Close database connection"""
        if self.use_json:
            self._save_json()
        elif self.pool:
            await self.pool.close()
