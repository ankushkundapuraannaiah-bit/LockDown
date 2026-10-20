import json
import os
from pathlib import Path

APP_NAME = "Lock Down"
APP_VERSION = "2.0.0"
APP_TAGLINE = "High-Security Editorial Browser with Brave Shields, Opera Workspaces & Zen Focus"

# Palette: Yellow & White — warm, modern, high-contrast sunshine theme
# Text tokens (dark text on white/yellow surfaces for crystal-clear readability)
COLOR_IVORY_LIGHT = "#18150E"      # Primary text color (deep charcoal)
COLOR_IVORY = "#2B2414"            # Secondary text color
COLOR_IVORY_DARK = "#4A3E1F"       # Muted text / dark accent
COLOR_IVORY_MUTED = "#6B5920"      # Subdued gold-brown text

# Surface hierarchy (Yellow & White layout)
COLOR_BLUE_DARKEST = "#FFFDF5"     # Main window & tab background (clean warm white)
COLOR_BLUE_DARK = "#FFF9D6"        # Toolbar / Navbar background (warm light yellow)
COLOR_BLUE_BASE = "#FFFFFF"        # Omnibox & card background (pure white)
COLOR_BLUE_SURFACE = "#FFF5B8"     # Surface cards / button base (soft cream-yellow)
COLOR_BLUE_BORDER = "#F0C000"      # Warm golden yellow border
COLOR_BLUE_HIGHLIGHT = "#FFDE59"   # Bright sunshine yellow highlight

# Accent: warm amber/orange for action buttons & active states
COLOR_CORAL_PRIMARY = "#E67300"
COLOR_CORAL_HOVER = "#F58700"
COLOR_CORAL_PRESSED = "#B85500"
COLOR_CORAL_GLOW = "rgba(230, 115, 0, 0.35)"

# Explicit Yellow & White color tokens
COLOR_TEXT_DARK = "#18150E"        # Near-black text
COLOR_TEXT_MED = "#4A3E1F"         # Medium brown text
COLOR_YELLOW_ACCENT = "#F0C000"    # Primary yellow border/accent
COLOR_YELLOW_BRIGHT = "#FFDE59"    # Bright yellow highlight
COLOR_YELLOW_SOFT = "#FFF9D6"      # Soft yellow background
COLOR_WHITE = "#FFFFFF"            # Pure clean white

# Modern Engine & HTTPS Standards
# UA matches Chrome 140 stable (native PyQt6 WebEngine version) — avoids bot detection
# and mismatch flags across Google, Cloudflare, Bing, DDG.
LATEST_CHROMIUM_VERSION = "140.0.0.0"
MODERN_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)

BASE_DIR = Path(__file__).resolve().parent.parent


def _is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def _is_usable_data_dir(path: Path) -> bool:
    return _is_writable_dir(path) and _is_writable_dir(path / "secure_vault")


def _resolve_user_data_dir() -> Path:
    override = os.environ.get("LOCKDOWN_USER_DATA_DIR", "").strip()
    candidates = []
    if override:
        candidates.append(Path(override).expanduser())
    candidates.append(Path(os.path.expanduser("~/.lockdown_browser")))
    candidates.append(BASE_DIR / ".lockdown_browser_data")
    candidates.append(BASE_DIR / ".lockdown_browser_runtime")

    for candidate in candidates:
        if _is_usable_data_dir(candidate):
            return candidate

    return BASE_DIR / ".lockdown_browser_runtime"


# Storage directories
USER_DATA_DIR = _resolve_user_data_dir()
VAULT_DIR = USER_DATA_DIR / "secure_vault"
EXTENSIONS_DIR = USER_DATA_DIR / "extensions"
LIBRARY_EXTENSIONS_DIR = BASE_DIR / "lockdown" / "extensions_library"
SETTINGS_FILE = USER_DATA_DIR / "settings.json"
BOOKMARKS_FILE = USER_DATA_DIR / "bookmarks.json"
NOTES_FILE = USER_DATA_DIR / "flow_notes.json"
DOWNLOADS_FILE = USER_DATA_DIR / "downloads.json"
LOCAL_VAULT_FILE = VAULT_DIR / "history.vault"
LOCAL_VAULT_META = VAULT_DIR / "vault_meta.json"
DOWNLOADS_DIR = Path.home() / "Downloads"

LOGO_ORIGINAL = BASE_DIR / "lockdown_logo.png"
LOGO_TRANSPARENT = BASE_DIR / "lockdown_logo_transparent.png"
LOGO_ICO = BASE_DIR / "lockdown_logo.ico"
ICONS_DIR = BASE_DIR / "icons"

# Search Engines - Clean standard endpoints prevent automated bot/CAPTCHA flags
SEARCH_ENGINES = {
    "Google": {
        "url": "https://www.google.com/search?q={query}",
        "home": "https://www.google.com",
    },
    "Brave Search": {
        "url": "https://search.brave.com/search?q={query}",
        "home": "https://search.brave.com",
    },
    "DuckDuckGo": {
        "url": "https://duckduckgo.com/?q={query}",
        "home": "https://duckduckgo.com",
    },
    "Bing": {
        "url": "https://www.bing.com/search?q={query}",
        "home": "https://www.bing.com",
    },
    "Ecosia": {
        "url": "https://www.ecosia.org/search?q={query}",
        "home": "https://www.ecosia.org",
    },
}

DEFAULT_SPEED_DIALS = [
    {
        "title": "Downloads",
        "url": "lockdown://downloads",
        "icon": "📥",
        "badge": "Files",
        "color": "#1890FF",
    },
    {
        "title": "Settings",
        "url": "lockdown://settings",
        "icon": "⚙️",
        "badge": "Config",
        "color": "#D48806",
    },
    {
        "title": "Extensions Hub",
        "url": "lockdown://extensions",
        "icon": "🧩",
        "badge": "Manager",
        "color": "#E67300",
    },
    {
        "title": "Brave Search",
        "url": "https://search.brave.com",
        "icon": "🦁",
        "badge": "Privacy",
        "color": "#FF6B4A",
    },
    {
        "title": "GitHub",
        "url": "https://github.com",
        "icon": "🐙",
        "badge": "Dev",
        "color": "#24292e",
    },
    {
        "title": "YouTube",
        "url": "https://www.youtube.com",
        "icon": "▶️",
        "badge": "Media",
        "color": "#FF0000",
    },
    {
        "title": "ChatGPT",
        "url": "https://chatgpt.com",
        "icon": "🤖",
        "badge": "AI",
        "color": "#10A37F",
    },
    {
        "title": "Reddit",
        "url": "https://www.reddit.com",
        "icon": "👾",
        "badge": "Social",
        "color": "#FF4500",
    },
    {
        "title": "Wikipedia",
        "url": "https://www.wikipedia.org",
        "icon": "📖",
        "badge": "Knowledge",
        "color": "#636466",
    },
    {
        "title": "Proton Mail",
        "url": "https://mail.proton.me",
        "icon": "🔒",
        "badge": "Secure",
        "color": "#6D4AFF",
    },
    {
        "title": "DuckDuckGo",
        "url": "https://duckduckgo.com",
        "icon": "🦆",
        "badge": "Search",
        "color": "#DE5833",
    },
]

DEFAULT_WORKSPACES = [
    {"id": "general", "name": "General", "icon": "🌐", "description": "Everyday Browsing"},
    {"id": "work", "name": "Work", "icon": "💼", "description": "Projects & Productivity"},
    {"id": "research", "name": "Research", "icon": "🔬", "description": "Deep Dives & Reading"},
    {"id": "media", "name": "Media", "icon": "🎬", "description": "Music & Entertainment"},
    {"id": "vault", "name": "Security", "icon": "🛡️", "description": "Confidential & Auditing"},
]

DEFAULT_SETTINGS = {
    "search_engine": "Google",  # Google gives the best desktop view with knowledge panel
    "home_url": "lockdown://home",
    "history_storage_mode": "local",  # "local" or "gdrive"
    "vault_password_set": False,
    "vault_salt": None,
    "vault_verifier": None,
    "gdrive_sync_enabled": False,
    "gdrive_folder_name": "LockDown_Secure_Vault",
    "gdrive_credentials_path": "",
    "shields_enabled": True,
    "ad_blocking": True,
    "tracker_blocking": True,
    "cookie_banner_blocking": True,
    "https_upgrade": True,
    "vpn_enabled": False,
    "vpn_server": "switzerland",
    "vpn_kill_switch": False,
    "vpn_protocol": "WireGuard",
    "vpn_custom_proxy": "",
    "zen_mode_enabled": False,
    "vertical_tabs": False,
    "hardware_acceleration": True,
    "doh_enabled": True,
    "doh_provider": "Cloudflare Privacy (1.1.1.1)",
    "gemini_api_key": "",
    "gemini_model": "gemini-2.5-flash",
    "gemini_view_browser": True,
    "gemini_temperature": 0.4,
    "gemini_system_prompt": "You are Lock Down AI Assistant, an advanced browsing intelligence powered by Google Gemini. You have real-time access to the user's active browser viewport and page context. Analyze what you see accurately, solve programming/technical problems step-by-step with clear code blocks, summarize long documents, and guide the user concisely.",
    "extensions_enabled": True,
    "download_directory": str(Path.home() / "Downloads"),
    "ask_download_location": False,
}


def load_settings():
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")


def load_bookmarks():
    if not BOOKMARKS_FILE.exists():
        initial = [
            {"title": "Brave Search", "url": "https://search.brave.com", "folder": "Default"},
            {"title": "Proton Privacy", "url": "https://proton.me", "folder": "Security"},
            {"title": "EFF Surveillance Self-Defense", "url": "https://ssd.eff.org", "folder": "Security"},
            {"title": "GitHub", "url": "https://github.com", "folder": "Development"},
        ]
        save_bookmarks(initial)
        return initial
    try:
        with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_bookmarks(bookmarks):
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
            json.dump(bookmarks, f, indent=2)
    except Exception as e:
        print(f"Error saving bookmarks: {e}")


def load_flow_notes():
    if not NOTES_FILE.exists():
        return []
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_flow_notes(notes):
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, indent=2)
    except Exception as e:
        print(f"Error saving notes: {e}")
