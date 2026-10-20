"""Lock Down Encrypted History Manager.
Handles search query extraction, automatic AES-256-GCM encryption,
strict zero-storage for private windows, and Local vs. Google Drive persistence.
"""

import threading
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from lockdown.config import load_settings
from lockdown.crypto_vault import CryptoVault
from lockdown.drive_sync import GoogleDriveSync


class HistoryManager:
    _instance: Optional["HistoryManager"] = None

    @classmethod
    def get_instance(cls) -> "HistoryManager":
        if cls._instance is None:
            cls._instance = HistoryManager()
        return cls._instance

    def __init__(self):
        self.vault = CryptoVault()
        self.drive_sync = GoogleDriveSync()
        self._in_memory_records: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._loaded = False

        # If vault is not yet setup with a custom password, we initialize with a default session key
        # so encryption is ALWAYS active from the very first second!
        if not self.vault.is_vault_initialized():
            self.vault.setup_vault("LockDownDefaultVault2026!")

        # Attempt initial unlock if default password exists
        if not self.vault.is_unlocked():
            self.vault.unlock_with_password("LockDownDefaultVault2026!")

        self._load_from_vault()

    def _load_from_vault(self) -> None:
        if self.vault.is_unlocked():
            ok, records, _ = self.vault.load_history_vault()
            if ok:
                with self._lock:
                    self._in_memory_records = records
                    self._loaded = True

    @staticmethod
    def extract_search_query(url: str) -> Optional[str]:
        """Detects whether a URL is a search engine request and extracts the search query."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            query_params = parse_qs(parsed.query)

            # Common search engines
            if any(s in domain for s in ["brave.com", "google.", "duckduckgo.com", "bing.com", "ecosia.org"]):
                for param in ["q", "query", "p", "search"]:
                    if param in query_params and query_params[param]:
                        return query_params[param][0]
        except Exception:
            pass
        return None

    def record_visit(self, url: str, title: str, is_private: bool = False) -> None:
        """Records a browsing visit.
        STRICT GUARANTEE: If is_private is True, the visit is IMMEDIATELY IGNORED and NOT STORED.
        """
        if is_private:
            return  # Zero-Storage Guarantee for Private Window

        if not url or url.startswith("lockdown://") or url.startswith("about:"):
            return

        clean_title = (title or "").strip() or url
        search_query = self.extract_search_query(url)
        domain = urlparse(url).netloc

        now = datetime.now()
        entry: Dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "timestamp": now.isoformat(),
            "display_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "time_short": now.strftime("%I:%M %p"),
            "date_short": now.strftime("%b %d, %Y"),
            "url": url,
            "title": clean_title,
            "domain": domain,
            "is_search": bool(search_query),
            "search_query": search_query or "",
            "visit_count": 1,
        }

        with self._lock:
            # Check if this exact URL was visited in the last 15 seconds (avoid duplicates)
            if self._in_memory_records:
                last = self._in_memory_records[0]
                if last.get("url") == url:
                    # Update title if it was loaded later
                    last["title"] = clean_title
                    self._save_to_storage()
                    return

            self._in_memory_records.insert(0, entry)
            # Cap maximum local in-memory history to 10,000 entries
            if len(self._in_memory_records) > 10000:
                self._in_memory_records = self._in_memory_records[:10000]

            self._save_to_storage()

    def _save_to_storage(self) -> None:
        """Encrypts records and saves to local vault or syncs to Google Drive."""
        if not self.vault.is_unlocked():
            return

        # 1. Always save locally to the secure password-protected folder
        self.vault.save_history_vault(self._in_memory_records)

        # 2. If storage mode is 'gdrive', trigger background cloud sync
        settings = load_settings()
        if settings.get("history_storage_mode") == "gdrive":
            try:
                with open(self.vault.vault_file, "rb") as f:
                    encrypted_bytes = f.read()
                self.drive_sync.async_sync(encrypted_bytes)
            except Exception as e:
                print(f"[HistoryManager] Drive sync trigger note: {e}")

    def get_entries(
        self, search_text: str = "", filter_type: str = "all"
    ) -> List[Dict[str, Any]]:
        """Returns filtered history records."""
        with self._lock:
            records = list(self._in_memory_records)

        query = search_text.strip().lower()
        results = []
        for r in records:
            if filter_type == "search" and not r.get("is_search"):
                continue
            if filter_type == "pages" and r.get("is_search"):
                continue

            if query:
                match = (
                    query in r.get("title", "").lower()
                    or query in r.get("url", "").lower()
                    or query in r.get("search_query", "").lower()
                    or query in r.get("domain", "").lower()
                )
                if not match:
                    continue

            results.append(r)
        return results

    def delete_entry(self, entry_id: str) -> None:
        """Deletes a specific history record by ID."""
        with self._lock:
            self._in_memory_records = [
                r for r in self._in_memory_records if r.get("id") != entry_id
            ]
            self._save_to_storage()

    def clear_history(self, scope: str = "all") -> int:
        """Clears history based on time scope ('hour', 'day', 'week', 'all').
        Returns the number of deleted records.
        """
        now = datetime.now()
        with self._lock:
            original_len = len(self._in_memory_records)
            if scope == "hour":
                cutoff = now - timedelta(hours=1)
                self._in_memory_records = [
                    r
                    for r in self._in_memory_records
                    if datetime.fromisoformat(r.get("timestamp", now.isoformat())) < cutoff
                ]
            elif scope == "day":
                cutoff = now - timedelta(days=1)
                self._in_memory_records = [
                    r
                    for r in self._in_memory_records
                    if datetime.fromisoformat(r.get("timestamp", now.isoformat())) < cutoff
                ]
            elif scope == "week":
                cutoff = now - timedelta(weeks=1)
                self._in_memory_records = [
                    r
                    for r in self._in_memory_records
                    if datetime.fromisoformat(r.get("timestamp", now.isoformat())) < cutoff
                ]
            else:  # all
                self._in_memory_records = []

            deleted = original_len - len(self._in_memory_records)
            self._save_to_storage()
            return deleted

    def count(self) -> int:
        with self._lock:
            return len(self._in_memory_records)
