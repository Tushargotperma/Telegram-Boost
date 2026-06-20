import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Config:
    """Application configuration settings."""
    
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    ADMIN_ID: int = int(os.getenv('ADMIN_ID', 0))
    FORCE_CHANNEL: str = os.getenv('FORCE_CHANNEL', '')
    SUPPORT_USERNAME: str = os.getenv('SUPPORT_USERNAME', '')
    WALLET_ADDRESS: str = os.getenv('WALLET_ADDRESS', '')
    
    PRICE_PER_BOOST: float = 0.80
    BOOST_OPTIONS: list = [4, 8, 12, 16, 20]
    
    @classmethod
    def validate(cls) -> bool:
        """Validate all required configuration variables are set."""
        required = ['BOT_TOKEN', 'ADMIN_ID', 'FORCE_CHANNEL', 'SUPPORT_USERNAME', 'WALLET_ADDRESS']
        missing = [var for var in required if not getattr(cls, var)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        if not cls.BOT_TOKEN.startswith('7'):
            raise ValueError("Invalid BOT_TOKEN format")
        
        return True
