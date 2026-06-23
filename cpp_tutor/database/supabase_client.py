"""Supabase client factory and lightweight data access helpers."""

from __future__ import annotations

import time
from functools import lru_cache
from typing import Any

from httpx import ReadError
from supabase import Client, create_client

from cpp_tutor.config import settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a singleton Supabase client instance."""
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    # Increase timeout for network stability
    if hasattr(client, 'session') and client.session:
        client.session.timeout = 30.0
    return client


class SupabaseRepository:
    """Repository adapter for common CRUD operations."""

    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase_client()

    @staticmethod
    def _retry_with_backoff(func, max_retries: int = 3):
        """Execute function with exponential backoff retry on network errors."""
        for attempt in range(max_retries):
            try:
                return func()
            except ReadError as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                time.sleep(wait_time)
            except Exception:
                raise

    def select(self, table: str, columns: str = "*", **filters: Any) -> list[dict[str, Any]]:
        """Fetch rows from table using equality filters."""
        def _do_select():
            query = self.client.table(table).select(columns)
            for key, value in filters.items():
                query = query.eq(key, value)
            response = query.execute()
            return response.data or []
        
        return self._retry_with_backoff(_do_select)

    def insert(self, table: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Insert one row and return inserted rows."""
        def _do_insert():
            response = self.client.table(table).insert(payload).execute()
            return response.data or []
        
        return self._retry_with_backoff(_do_insert)

    def upsert(self, table: str, payload: dict[str, Any], on_conflict: str | None = None) -> list[dict[str, Any]]:
        """Upsert one row and return affected rows."""
        def _do_upsert():
            if on_conflict:
                response = self.client.table(table).upsert(payload, on_conflict=on_conflict).execute()
            else:
                response = self.client.table(table).upsert(payload).execute()
            return response.data or []
        
        return self._retry_with_backoff(_do_upsert)

    def update(self, table: str, payload: dict[str, Any], **filters: Any) -> list[dict[str, Any]]:
        """Update rows by equality filters."""
        def _do_update():
            query = self.client.table(table).update(payload)
            for key, value in filters.items():
                query = query.eq(key, value)
            response = query.execute()
            return response.data or []
        
        return self._retry_with_backoff(_do_update)
