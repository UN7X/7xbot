import os
from dataclasses import dataclass
from typing import List

@dataclass
class Config:
    """Bot configuration"""
    DEFAULT_PREFIX: str = os.getenv('DEFAULT_PREFIX', '!')
    OWNER_IDS: List[int] = None
    
    # Colors
    PRIMARY_COLOR: int = 0x3498db
    SUCCESS_COLOR: int = 0x2ecc71
    ERROR_COLOR: int = 0xe74c3c
    WARNING_COLOR: int = 0xf39c12
    
    # Economy
    DAILY_REWARD: int = int(os.getenv('DAILY_REWARD', 100))
    WORK_REWARD_MIN: int = int(os.getenv('WORK_REWARD_MIN', 50))
    WORK_REWARD_MAX: int = int(os.getenv('WORK_REWARD_MAX', 200))
    
    # Leveling
    XP_PER_MESSAGE: int = int(os.getenv('XP_PER_MESSAGE', 15))
    XP_COOLDOWN: int = int(os.getenv('XP_COOLDOWN', 60))  # seconds
    
    # Music
    MAX_QUEUE_SIZE: int = int(os.getenv('MAX_QUEUE_SIZE', 100))
    MAX_SONG_LENGTH: int = int(os.getenv('MAX_SONG_LENGTH', 600))  # seconds
    
    def __post_init__(self):
        owner_id = os.getenv('OWNER_ID')
        if owner_id:
            self.OWNER_IDS = [int(owner_id)]
        else:
            self.OWNER_IDS = []
        
        # Add additional owners from comma-separated env var
        additional_owners = os.getenv('ADDITIONAL_OWNER_IDS', '')
        if additional_owners:
            for owner in additional_owners.split(','):
                if owner.strip():
                    self.OWNER_IDS.append(int(owner.strip()))
