# backend/app/core/supabase_client.py
"""
Async DB connection helpers.
Uses asyncpg pool. Reads DATABASE_URL (or SUPABASE_DB_URL) from environment.
"""
import os
import asyncpg
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
backend_dir = Path(__file__).parent.parent.parent
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")

# Make SSL configurable via environment variable
DB_SSL = os.getenv("DB_SSL", "require")  # 'require', 'prefer', or 'disable'

_pool: Optional[asyncpg.pool.Pool] = None

async def init_db_pool(min_size: int = 1, max_size: int = 10):
    """
    Initialize the global asyncpg connection pool.
    
    Args:
        min_size: Minimum number of connections to maintain
        max_size: Maximum number of connections allowed
        
    Returns:
        The initialized connection pool
        
    Raises:
        ValueError: If DATABASE_URL is not configured
    """
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise ValueError(
                "DATABASE_URL not configured. Please set DATABASE_URL in your .env file.\n"
                "Required format: postgresql://postgres.PROJECT_REF:PASSWORD@HOST:5432/postgres\n"
                "See docs/DAY2_QUICK_START.md for setup instructions."
            )
        
        # Configure SSL based on environment
        ssl_config = DB_SSL if DB_SSL in ['require', 'prefer', 'disable'] else 'require'
        
        try:
            _pool = await asyncpg.create_pool(
                dsn=DATABASE_URL, 
                min_size=min_size, 
                max_size=max_size, 
                ssl=ssl_config,
                command_timeout=60
            )
            print(f"✅ Database pool initialized (min={min_size}, max={max_size}, ssl={ssl_config})")
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize database pool: {e}\n"
                f"DATABASE_URL configured: {bool(DATABASE_URL)}\n"
                f"SSL mode: {ssl_config}\n"
                f"Hint: Check your connection string and network connectivity."
            ) from e
            
    return _pool


async def get_conn():
    """
    Get the global connection pool. Initializes it if not already done.
    
    Usage:
        pool = await get_conn()
        async with pool.acquire() as conn:
            result = await conn.fetch("SELECT * FROM table")
            
    Returns:
        The global asyncpg connection pool
    """
    global _pool
    if _pool is None:
        await init_db_pool()
    return _pool


async def close_pool():
    """
    Close the global connection pool. Should be called on application shutdown.
    """
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        print("✅ Database pool closed")
