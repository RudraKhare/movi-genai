"""
Database connection and session management for Movi backend.
Supports both Supabase and local PostgreSQL connections.
"""
import os
import re
from pathlib import Path
from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables from backend/.env explicitly
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Loaded .env from: {env_path}")
else:
    print(f"⚠️  .env file not found at: {env_path}")
    # Try loading from current directory as fallback
    load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Validate required environment variables
if not DATABASE_URL:
    raise ValueError(
        "❌ DATABASE_URL not found in environment variables.\n"
        "Please ensure .env file exists with DATABASE_URL set."
    )

# Function to mask password in URL for safe logging
def mask_password(url: str) -> str:
    """Mask password in database URL for safe logging."""
    try:
        parsed = urlparse(url)
        if parsed.password:
            masked = url.replace(parsed.password, "*****")
            return masked
    except Exception:
        pass
    return url[:20] + "*****" + url[-20:]

# Convert postgres:// to postgresql+asyncpg:// for async support
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Parse URL for logging and SSL configuration
parsed_url = urlparse(DATABASE_URL)

# Remove any existing sslmode parameter from query string (asyncpg doesn't support it)
query_params = parse_qs(parsed_url.query)
if "sslmode" in query_params:
    del query_params["sslmode"]
    new_query = urlencode(query_params, doseq=True)
    DATABASE_URL = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        new_query,
        parsed_url.fragment
    ))
    parsed_url = urlparse(DATABASE_URL)  # Re-parse after modification

# Log connection details (with masked password)
print(f"📦 DATABASE_URL: {mask_password(DATABASE_URL)}")
print(f"🌐 Connecting to host: {parsed_url.hostname}")

# Configure SSL for Supabase connections
connect_args = {}
if "supabase.co" in (parsed_url.hostname or ""):
    # asyncpg requires ssl=True or an SSL context, not sslmode=require
    connect_args["ssl"] = "require"
    print(f"🔒 SSL mode: require (via connect_args)")
    
    # Force IPv6 resolution for Supabase (some regions only support IPv6)
    # This helps resolve DNS issues on Windows
    try:
        import socket
        # Check if host resolves to IPv6
        addr_info = socket.getaddrinfo(parsed_url.hostname, parsed_url.port or 5432, 
                                       socket.AF_UNSPEC, socket.SOCK_STREAM)
        has_ipv6 = any(info[0] == socket.AF_INET6 for info in addr_info)
        has_ipv4 = any(info[0] == socket.AF_INET for info in addr_info)
        
        if has_ipv6 and not has_ipv4:
            print(f"ℹ️  Host uses IPv6 only, configuring connection...")
            # asyncpg will handle IPv6 automatically, but we ensure it's enabled
    except Exception as e:
        print(f"⚠️  DNS pre-check warning: {e}")

# Create async engine with SSL configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    future=True,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=10,
    max_overflow=20,
    connect_args=connect_args,  # Pass SSL configuration here
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    Use in FastAPI endpoints with Depends(get_db).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()



async def test_connection() -> bool:
    """
    Test database connection.
    Returns True if connection is successful, False otherwise.
    """
    try:
        print("🔌 Testing database connection...")
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Provide helpful error messages
        error_str = str(e)
        if "getaddrinfo failed" in error_str or "11001" in error_str:
            print("\n💡 Troubleshooting:")
            print("   1. Check if sslmode=require is in your DATABASE_URL")
            print("   2. Verify your internet connection")
            print("   3. Ensure the Supabase host is reachable")
            print(f"   4. Try: ping {parsed_url.netloc.split(':')[0]}")
        elif "password authentication failed" in error_str:
            print("\n💡 Check your database password in DATABASE_URL")
        elif "database" in error_str and "does not exist" in error_str:
            print("\n💡 The specified database does not exist on the server")
        
        return False



def get_supabase_client():
    """
    Get Supabase client for direct API access (alternative to SQL).
    Useful for real-time subscriptions and auth.
    """
    from supabase import create_client, Client
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required for Supabase client"
        )
    
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return supabase
