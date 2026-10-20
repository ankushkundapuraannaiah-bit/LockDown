"""Lock Down Search Engine Autocomplete & Suggestions Engine.
Fetches real-time search suggestions from Google, DuckDuckGo, Bing, Brave, and Ecosia.
Supports asynchronous thread-safe querying with seamless fallback.
"""

import json
import threading
from urllib.parse import quote_plus
import urllib.request
from typing import List, Optional

from lockdown.qt_compat import QObject, pyqtSignal


def get_suggestion_endpoint(engine_name: str, query: str) -> str:
    q = quote_plus(query)
    engine = engine_name.strip()
    if engine == "DuckDuckGo":
        return f"https://duckduckgo.com/ac/?q={q}&type=list"
    elif engine == "Bing":
        return f"https://api.bing.com/osjson.aspx?query={q}"
    elif engine == "Ecosia":
        return f"https://ac.ecosia.org/autocomplete?q={q}&type=list"
    elif engine == "Brave Search":
        return f"https://search.brave.com/api/suggest?q={q}"
    else:  # Google default - client=firefox avoids Chrome-token verification/rate-limit bot flags
        return f"https://suggestqueries.google.com/complete/search?client=firefox&q={q}"


def fetch_search_suggestions(query: str, engine_name: str = "Google", max_results: int = 8) -> List[str]:
    """Fetch search suggestions synchronously from the search engine API."""
    query = query.strip()
    if not query:
        return []

    endpoints = [get_suggestion_endpoint(engine_name, query)]
    # Fallback to DuckDuckGo and Google if primary engine is rate-limited or fails
    if engine_name not in ("Google", "DuckDuckGo"):
        endpoints.append(f"https://duckduckgo.com/ac/?q={quote_plus(query)}&type=list")
        endpoints.append(f"https://suggestqueries.google.com/complete/search?client=firefox&q={quote_plus(query)}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    for url in endpoints:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=1.8) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                # OpenSearch format: [query, [suggestions, ...], ...]
                if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
                    results = [str(item) for item in data[1] if item]
                    return results[:max_results]
        except Exception:
            continue

    return []


class SuggestionFetcher(QObject):
    suggestions_ready = pyqtSignal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_query = ""
        self._lock = threading.Lock()

    def request_suggestions(self, query: str, engine_name: str = "Google"):
        query = query.strip()
        with self._lock:
            self._current_query = query

        if not query:
            self.suggestions_ready.emit("", [])
            return

        def worker():
            results = fetch_search_suggestions(query, engine_name)
            with self._lock:
                if self._current_query == query:
                    self.suggestions_ready.emit(query, results)

        t = threading.Thread(target=worker, daemon=True)
        t.start()
