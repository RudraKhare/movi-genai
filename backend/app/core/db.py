# backend/app/core/db.py
"""
Low-level query helpers wrapping asyncpg pool/connection.
Provides convenience functions used by service layer.
"""
from .supabase_client import get_conn
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager


async def fetchrow(query: str, *args) -> Optional[Dict[str, Any]]:
    """
    Execute a query and return a single row as a dictionary.
    
    Args:
        query: SQL query with $1, $2, etc. placeholders
        *args: Query parameters
        
    Returns:
        Dictionary of column->value, or None if no row found
    """
    pool = await get_conn()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def fetch(query: str, *args) -> List[Dict[str, Any]]:
    """
    Execute a query and return all rows as a list of dictionaries.
    
    Args:
        query: SQL query with $1, $2, etc. placeholders
        *args: Query parameters
        
    Returns:
        List of dictionaries, one per row
    """
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(r) for r in rows]


async def execute(query: str, *args) -> str:
    """
    Execute a query that doesn't return rows (INSERT, UPDATE, DELETE).
    
    Args:
        query: SQL query with $1, $2, etc. placeholders
        *args: Query parameters
        
    Returns:
        Status string from the database (e.g., "INSERT 0 1")
    """
    pool = await get_conn()
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


@asynccontextmanager
async def transaction():
    """
    Context manager for atomic transactions.
    
    Ensures all operations within the context either commit together or rollback on error.
    
    Usage:
        async with transaction() as conn:
            await conn.execute("INSERT INTO ...")
            await conn.execute("UPDATE ...")
            # Automatically commits on success, rolls back on exception
            
    Yields:
        asyncpg Connection object for executing queries within the transaction
    """
    pool = await get_conn()
    async with pool.acquire() as conn:
        tr = conn.transaction()
        await tr.start()
        try:
            yield conn
            await tr.commit()
        except Exception:
            await tr.rollback()
            raise


async def fetchval(query: str, *args) -> Any:
    """
    Execute a query and return a single scalar value.
    
    Useful for COUNT queries, EXISTS checks, etc.
    
    Args:
        query: SQL query with $1, $2, etc. placeholders
        *args: Query parameters
        
    Returns:
        The first column of the first row, or None if no result
    """
    pool = await get_conn()
    async with pool.acquire() as conn:
        return await conn.fetchval(query, *args)
