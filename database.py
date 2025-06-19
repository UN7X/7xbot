import asyncpg
import asyncio
from typing import Optional, List, Dict, Any
import json
import os
from urllib.parse import urlparse

class Database:
    def __init__(self):
        self.pool = None
        self.connection_url = os.getenv('DATABASE_URL')
        
        # Handle Heroku's updated DATABASE_URL format if needed
        if self.connection_url and self.connection_url.startswith('postgres://'):
            self.connection_url = self.connection_url.replace('postgres://', 'postgresql://', 1)
    
    async def setup(self):
        """Initialize database and create tables"""
        self.pool = await asyncpg.create_pool(self.connection_url)
        
        # Guild settings
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS guilds (
                id BIGINT PRIMARY KEY,
                prefix TEXT DEFAULT '!',
                welcome_channel BIGINT,
                log_channel BIGINT,
                automod_enabled BOOLEAN DEFAULT FALSE,
                settings JSONB DEFAULT '{}'::jsonb
            )
        """)
        
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
        result = await self.pool.fetchrow(
            "SELECT prefix FROM guilds WHERE id = $1", guild_id
        )
        return result['prefix'] if result else None
    
    async def set_guild_prefix(self, guild_id: int, prefix: str):
        """Set guild's custom prefix"""
        await self.pool.execute(
            """
            INSERT INTO guilds (id, prefix) 
            VALUES ($1, $2)
            ON CONFLICT (id) DO UPDATE SET prefix = $2
            """,
            guild_id, prefix
        )
    
    async def setup_guild(self, guild_id: int):
        """Setup a new guild in database"""
        await self.pool.execute(
            """
            INSERT INTO guilds (id) 
            VALUES ($1)
            ON CONFLICT (id) DO NOTHING
            """, 
            guild_id
        )
    
    async def get_balance(self, user_id: int, guild_id: int) -> Dict[str, int]:
        """Get user's economy balance"""
        result = await self.pool.fetchrow(
            "SELECT balance, bank FROM economy WHERE user_id = $1 AND guild_id = $2",
            user_id, guild_id
        )
        if result:
            return {"balance": result['balance'], "bank": result['bank']}
        return {"balance": 0, "bank": 0}
    
    async def update_balance(self, user_id: int, guild_id: int, amount: int):
        """Update user's balance"""
        await self.pool.execute("""
            INSERT INTO economy (user_id, guild_id, balance, bank)
            VALUES ($1, $2, $3, 0)
            ON CONFLICT (user_id, guild_id) DO UPDATE 
            SET balance = economy.balance + $3
        """, user_id, guild_id, amount)
    
    async def get_user_level(self, user_id: int, guild_id: int) -> Dict[str, int]:
        """Get user's level and XP"""
        result = await self.pool.fetchrow(
            "SELECT xp, level FROM levels WHERE user_id = $1 AND guild_id = $2",
            user_id, guild_id
        )
        if result:
            return {"xp": result['xp'], "level": result['level']}
        return {"xp": 0, "level": 0}
    
    async def add_xp(self, user_id: int, guild_id: int, xp: int) -> bool:
        """Add XP to user and return True if leveled up"""
        current = await self.get_user_level(user_id, guild_id)
        new_xp = current["xp"] + xp
        new_level = int(new_xp ** (1/4))  # Level formula
        
        await self.pool.execute("""
            INSERT INTO levels (user_id, guild_id, xp, level, last_message)
            VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, guild_id) DO UPDATE
            SET xp = $3, level = $4, last_message = CURRENT_TIMESTAMP
        """, user_id, guild_id, new_xp, new_level)
        
        return new_level > current["level"]
    
    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str):
        """Add a warning to user"""
        await self.pool.execute("""
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
            VALUES ($1, $2, $3, $4)
        """, guild_id, user_id, moderator_id, reason)
    
    async def get_warnings(self, guild_id: int, user_id: int) -> List[Dict]:
        """Get user's warnings"""
        results = await self.pool.fetch("""
            SELECT id, moderator_id, reason, timestamp FROM warnings
            WHERE guild_id = $1 AND user_id = $2
            ORDER BY timestamp DESC
        """, guild_id, user_id)
        
        return [
            {
                "id": row['id'],
                "moderator_id": row['moderator_id'],
                "reason": row['reason'],
                "timestamp": row['timestamp']
            }
            for row in results
        ]
    
    async def close(self):
        """Close database connection"""
        if self.pool:
            await self.pool.close()
