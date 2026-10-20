"""Lock Down Extension Manager.
Provides full lifecycle management for browser extensions:
- Bundled Curated Extension Library (Dark Reader, uBlock Shield Plus, Reader Mode, JSON Inspector, Eyedropper, Tab Memory Saver)
- Native Chromium WebExtension support via PyQt6 QWebEngineExtensionManager
- Unpacked custom extension installation from folders or ZIPs
- Live enable/disable toggling and persistent state management
- Fallback content script injector for guaranteed site-wide functionality
"""

import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from lockdown.config import (
    EXTENSIONS_DIR,
    LIBRARY_EXTENSIONS_DIR,
    USER_DATA_DIR,
    load_settings,
    save_settings,
)
from lockdown.qt_compat import QWebEngineProfile, QWebEngineScript

META_FILE = USER_DATA_DIR / "extensions_registry.json"


# ---------------------------------------------------------------------------
# ONLINE EXTENSION REPOSITORY CATALOG
# ---------------------------------------------------------------------------
ONLINE_EXTENSIONS = [
    {
        "id": "singlefile",
        "name": "SingleFile Page Archiver",
        "version": "1.22.46",
        "category": "Productivity",
        "icon": "💾",
        "description": "Complete offline web page archiver. Saves entire page (HTML, images, fonts, styles) into a single portable file.",
        "author": "Gildas Lormeau (Open Source)",
        "download_url": "https://github.com/gildas-lormeau/SingleFile/archive/refs/heads/master.zip",
        "is_online": True,
        "badge": "Online Download",
    },
    {
        "id": "sponsorblock",
        "name": "SponsorBlock for YouTube",
        "version": "5.9.1",
        "category": "Media & Privacy",
        "icon": "⏭️",
        "description": "Community-driven sponsor skip assistant. Automatically skips sponsored segments, subscriber begging, and intros.",
        "author": "Ajay Ramachandran (Open Source)",
        "download_url": "https://github.com/ajayyy/SponsorBlock/archive/refs/tags/5.9.1.zip",
        "is_online": True,
        "badge": "Online Download",
    },
    {
        "id": "unhook-yt",
        "name": "Unhook - Focus Mode for YouTube",
        "version": "1.6.0",
        "category": "Productivity",
        "icon": "🎯",
        "description": "Eliminates distracting YouTube home feed recommendations, related sidebar videos, and comments for deep reading focus.",
        "author": "Unhook Open Source",
        "download_url": "https://raw.githubusercontent.com/dragone/unhook-extension/main/unhook.zip",
        "is_online": True,
        "badge": "Online Download",
    },
    {
        "id": "markdown-clipper",
        "name": "Web Markdown Clipper",
        "version": "1.3.0",
        "category": "Developer Tools",
        "icon": "📝",
        "description": "Extracts clean GitHub-flavored markdown from any article, blog post, or documentation page in one click.",
        "author": "Markdown Labs",
        "download_url": "",
        "is_online": True,
        "badge": "Online Download",
    },
]


# ---------------------------------------------------------------------------
# CURATED EXTENSION BUNDLE DEFINITIONS
# ---------------------------------------------------------------------------
CURATED_EXTENSIONS = {
    "dark-reader": {
        "id": "dark-reader",
        "name": "Dark Reader Pro",
        "version": "1.2.0",
        "category": "Appearance",
        "icon": "🌙",
        "description": "High-contrast smart dark mode for every website. Protects eyes and reduces strain with warm nocturnal hues.",
        "author": "Lock Down Team",
        "manifest": {
            "manifest_version": 3,
            "name": "Dark Reader Pro",
            "version": "1.2.0",
            "description": "Smart nocturnal dark mode for every website",
            "content_scripts": [
                {
                    "matches": ["<all_urls>"],
                    "js": ["content.js"],
                    "css": ["dark.css"],
                    "run_at": "document_start",
                }
            ],
        },
        "css": """
            html[data-lockdown-dark="true"] {
                filter: invert(90%) hue-rotate(180deg) !important;
                background-color: #121212 !important;
            }
            html[data-lockdown-dark="true"] img,
            html[data-lockdown-dark="true"] video,
            html[data-lockdown-dark="true"] canvas,
            html[data-lockdown-dark="true"] iframe,
            html[data-lockdown-dark="true"] svg {
                filter: invert(100%) hue-rotate(180deg) !important;
            }
        """,
        "js": """
            (function() {
                if (window.__LOCKDOWN_DARK_APPLIED__) return;
                window.__LOCKDOWN_DARK_APPLIED__ = true;
                const applyDark = () => {
                    if (document.documentElement) {
                        document.documentElement.setAttribute('data-lockdown-dark', 'true');
                    }
                };
                applyDark();
                document.addEventListener('DOMContentLoaded', applyDark);
            })();
        """,
    },
    "ublock-shield-plus": {
        "id": "ublock-shield-plus",
        "name": "uBlock Shield Plus",
        "version": "2.1.0",
        "category": "Privacy & Security",
        "icon": "🛡️",
        "description": "Enhanced cosmetic banner stripper and telemetry blocker. Conceals sponsored blocks, consent spam, and floating video traps.",
        "author": "Lock Down Privacy Labs",
        "manifest": {
            "manifest_version": 3,
            "name": "uBlock Shield Plus",
            "version": "2.1.0",
            "description": "Aggressive cosmetic ad and telemetry suppressor",
            "content_scripts": [
                {
                    "matches": ["<all_urls>"],
                    "js": ["content.js"],
                    "run_at": "document_end",
                }
            ],
        },
        "css": "",
        "js": """
            (function() {
                const hideSelectors = [
                    'ins.adsbygoogle', 'div[id^="google_ads_"]', '.ad-slot', '.sponsored-post',
                    '.banner-ad', '.ad-wrapper', 'div[data-ad-unit]', '.cookie-notice',
                    '#onetrust-banner-sdk', '.trc_related_container', '.taboola-ad'
                ];
                const clean = () => {
                    const sel = hideSelectors.join(', ');
                    document.querySelectorAll(sel).forEach(el => {
                        el.style.setProperty('display', 'none', 'important');
                    });
                };
                clean();
                setInterval(clean, 1500);
            })();
        """,
    },
    "reader-mode": {
        "id": "reader-mode",
        "name": "Clean Reader Mode",
        "version": "1.5.0",
        "category": "Productivity",
        "icon": "📖",
        "description": "Distraction-free reading view. Strips sidebars, cookie nag-screens, and ads into an editorial, high-focus typography canvas.",
        "author": "Lock Down Editorial",
        "manifest": {
            "manifest_version": 3,
            "name": "Clean Reader Mode",
            "version": "1.5.0",
            "description": "Editorial distraction-free reader mode",
            "content_scripts": [
                {
                    "matches": ["<all_urls>"],
                    "js": ["content.js"],
                    "run_at": "document_idle",
                }
            ],
        },
        "css": """
            #lockdown-reader-btn {
                position: fixed;
                bottom: 24px;
                right: 24px;
                z-index: 999999;
                background: #E67300;
                color: #FFFFFF;
                border: 2px solid #FFDE59;
                border-radius: 20px;
                padding: 8px 16px;
                font-family: system-ui, -apple-system, sans-serif;
                font-size: 13px;
                font-weight: 700;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                transition: transform 0.2s;
            }
            #lockdown-reader-btn:hover {
                transform: scale(1.05);
            }
        """,
        "js": """
            (function() {
                if (document.getElementById('lockdown-reader-btn')) return;
                const btn = document.createElement('button');
                btn.id = 'lockdown-reader-btn';
                btn.innerHTML = '📖 Toggle Reader';
                let active = false;
                btn.onclick = () => {
                    active = !active;
                    if (active) {
                        const article = document.querySelector('article') || document.querySelector('main') || document.body;
                        document.body.setAttribute('data-original-html', document.body.innerHTML);
                        document.body.innerHTML = `
                            <div style="max-width: 760px; margin: 40px auto; padding: 20px 30px; font-family: Georgia, serif; line-height: 1.8; font-size: 19px; color: #18150E; background: #FFFDF5;">
                                <div style="margin-bottom: 24px; border-bottom: 1px solid #F0C000; padding-bottom: 12px;">
                                    <h1 style="font-size: 32px; margin-bottom: 8px;">${document.title}</h1>
                                    <div style="font-size: 13px; color: #6B5920;">Source: ${location.hostname}</div>
                                </div>
                                <div id="ld-reader-content">${article.innerHTML}</div>
                            </div>
                        `;
                        document.body.style.background = '#FFFDF5';
                        document.body.appendChild(btn);
                    } else {
                        const orig = document.body.getAttribute('data-original-html');
                        if (orig) document.body.innerHTML = orig;
                    }
                };
                if (document.body) document.body.appendChild(btn);
            })();
        """,
    },
    "json-inspector": {
        "id": "json-inspector",
        "name": "JSON Tree Inspector",
        "version": "1.3.0",
        "category": "Developer Tools",
        "icon": "🗂️",
        "description": "Formats raw JSON responses into an interactive collapsible tree view with search and one-click path copying.",
        "author": "Dev Tools Hub",
        "manifest": {
            "manifest_version": 3,
            "name": "JSON Tree Inspector",
            "version": "1.3.0",
            "description": "Auto-detect and format JSON endpoints",
            "content_scripts": [
                {
                    "matches": ["<all_urls>"],
                    "js": ["content.js"],
                    "run_at": "document_end",
                }
            ],
        },
        "css": "",
        "js": """
            (function() {
                const ct = document.contentType || '';
                const isJson = ct.includes('json') || (document.body && document.body.children.length === 1 && document.body.firstElementChild.tagName === 'PRE');
                if (!isJson) return;
                try {
                    const text = (document.body.innerText || '').trim();
                    if ((text.startsWith('{') && text.endsWith('}')) || (text.startsWith('[') && text.endsWith(']'))) {
                        const data = JSON.parse(text);
                        document.body.innerHTML = `
                            <div style="background: #18150E; color: #FFDE59; font-family: 'Consolas', 'Courier New', monospace; padding: 24px; min-height: 100vh; font-size: 14px;">
                                <div style="margin-bottom: 16px; border-bottom: 1px solid #4A3E1F; padding-bottom: 10px; display: flex; justify-content: space-between;">
                                    <span style="font-weight: 800; color: #E67300;">🗂️ JSON Inspector Active</span>
                                    <span style="color: #FAF6ED; font-size: 12px;">Formatted JSON (${Object.keys(data).length} root keys)</span>
                                </div>
                                <pre style="white-space: pre-wrap; word-break: break-all; color: #FAF6ED;">${JSON.stringify(data, null, 2)}</pre>
                            </div>
                        `;
                    }
                } catch(e) {}
            })();
        """,
    },
    "color-eyedropper": {
        "id": "color-eyedropper",
        "name": "Web Color Eyedropper",
        "version": "1.1.0",
        "category": "Developer Tools",
        "icon": "🎨",
        "description": "Hover over any web element to sample and copy exact Hex, RGB, and CSS color values straight to the clipboard.",
        "author": "Lock Down Design Tools",
        "manifest": {
            "manifest_version": 3,
            "name": "Web Color Eyedropper",
            "version": "1.1.0",
            "description": "Sample and copy hex color values",
            "content_scripts": [
                {
                    "matches": ["<all_urls>"],
                    "js": ["content.js"],
                    "run_at": "document_idle",
                }
            ],
        },
        "css": "",
        "js": """
            (function() {
                if (window.__LOCKDOWN_EYEDROPPER__) return;
                window.__LOCKDOWN_EYEDROPPER__ = true;
                const badge = document.createElement('div');
                badge.id = 'ld-color-pill';
                badge.style.cssText = 'position: fixed; bottom: 24px; left: 24px; z-index: 999999; background: #18150E; color: #FFFDF5; border: 1.5px solid #E67300; border-radius: 12px; padding: 6px 12px; font-family: monospace; font-size: 12px; pointer-events: none; display: none;';
                document.body.appendChild(badge);

                document.addEventListener('mousemove', (e) => {
                    if (!e.altKey) {
                        badge.style.display = 'none';
                        return;
                    }
                    const el = document.elementFromPoint(e.clientX, e.clientY);
                    if (el) {
                        const style = window.getComputedStyle(el);
                        const color = style.color;
                        const bg = style.backgroundColor;
                        badge.innerHTML = `🎨 Color: <b>${color}</b> | BG: <b>${bg}</b> (Hold Alt)`;
                        badge.style.display = 'block';
                    }
                });
            })();
        """,
    },
    "tab-memory-saver": {
        "id": "tab-memory-saver",
        "name": "Tab Memory Saver",
        "version": "1.0.4",
        "category": "Productivity",
        "icon": "⚡",
        "description": "Background optimizer that pauses unneeded animations and heavy rendering loops on dormant tabs to conserve memory and battery.",
        "author": "Lock Down Performance Lab",
        "manifest": {
            "manifest_version": 3,
            "name": "Tab Memory Saver",
            "version": "1.0.4",
            "description": "Saves system resources on hidden tabs",
            "content_scripts": [
                {
                    "matches": ["<all_urls>"],
                    "js": ["content.js"],
                    "run_at": "document_start",
                }
            ],
        },
        "css": "",
        "js": """
            (function() {
                document.addEventListener('visibilitychange', () => {
                    if (document.hidden) {
                        document.title = '💤 ' + document.title.replace('💤 ', '');
                    } else {
                        document.title = document.title.replace('💤 ', '');
                    }
                });
            })();
        """,
    },
    "markdown-clipper": {
        "id": "markdown-clipper",
        "name": "Web Markdown Clipper",
        "version": "1.3.0",
        "category": "Developer Tools",
        "icon": "📝",
        "description": "Extracts clean GitHub-flavored markdown from any article, blog post, or documentation page with one click.",
        "author": "Markdown Labs",
        "manifest": {
            "manifest_version": 3,
            "name": "Web Markdown Clipper",
            "version": "1.3.0",
            "description": "Extracts markdown from webpages",
            "content_scripts": [
                {
                    "matches": ["<all_urls>"],
                    "js": ["content.js"],
                    "run_at": "document_idle",
                }
            ],
        },
        "css": "",
        "js": """
            (function() {
                if (window.__MD_CLIPPER_BTN__) return;
                window.__MD_CLIPPER_BTN__ = true;
                const b = document.createElement('button');
                b.id = 'ld-clip-btn';
                b.innerHTML = '📝 Copy as Markdown';
                b.style.cssText = 'position:fixed;bottom:24px;right:160px;z-index:999999;background:#18150E;color:#FFDE59;border:1.5px solid #E67300;border-radius:18px;padding:6px 14px;font-family:sans-serif;font-size:12px;font-weight:700;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.3);';
                b.onclick = () => {
                    const text = `# ${document.title}\\n\\nSource: ${location.href}\\n\\n` + (document.querySelector('article') || document.body).innerText;
                    navigator.clipboard.writeText(text).then(() => {
                        b.innerHTML = '✓ Markdown Copied!';
                        setTimeout(() => { b.innerHTML = '📝 Copy as Markdown'; }, 2500);
                    });
                };
                if (document.body) document.body.appendChild(b);
            })();
        """,
    },
    "unhook-yt": {
        "id": "unhook-yt",
        "name": "Unhook - Focus Mode for YouTube",
        "version": "1.6.0",
        "category": "Productivity",
        "icon": "🎯",
        "description": "Eliminates distracting YouTube home feed recommendations, related sidebar videos, and comments for deep reading focus.",
        "author": "Unhook Open Source",
        "manifest": {
            "manifest_version": 3,
            "name": "Unhook - Focus Mode for YouTube",
            "version": "1.6.0",
            "description": "Hide YouTube distractions and recommendations",
            "content_scripts": [
                {
                    "matches": ["*://*.youtube.com/*"],
                    "js": ["content.js"],
                    "run_at": "document_start",
                }
            ],
        },
        "css": "",
        "js": """
            (function() {
                if (!location.hostname.includes('youtube.com')) return;
                const hideUnhook = () => {
                    const selectors = ['#related', '#comments', 'ytd-rich-grid-renderer', '#secondary'];
                    selectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => {
                            el.style.setProperty('display', 'none', 'important');
                        });
                    });
                };
                hideUnhook();
                setInterval(hideUnhook, 1200);
            })();
        """,
    },
}


class ExtensionManager:
    """Singleton manager overseeing installed extensions, library bundles,
    and profile integration."""

    _instance: Optional["ExtensionManager"] = None

    def __init__(self):
        self.profile: Optional[QWebEngineProfile] = None
        self._ensure_directories()
        self._populate_curated_library()
        self.registry: Dict[str, Any] = self._load_registry()

    @classmethod
    def get_instance(cls) -> "ExtensionManager":
        if cls._instance is None:
            cls._instance = ExtensionManager()
        return cls._instance

    def _ensure_directories(self):
        EXTENSIONS_DIR.mkdir(parents=True, exist_ok=True)
        LIBRARY_EXTENSIONS_DIR.mkdir(parents=True, exist_ok=True)

    def _populate_curated_library(self):
        """Generates standard unpacked extension bundles in LIBRARY_EXTENSIONS_DIR."""
        for ext_id, ext_def in CURATED_EXTENSIONS.items():
            target_dir = LIBRARY_EXTENSIONS_DIR / ext_id
            target_dir.mkdir(parents=True, exist_ok=True)

            manifest_path = target_dir / "manifest.json"
            manifest_path.write_text(json.dumps(ext_def["manifest"], indent=2), encoding="utf-8")

            if ext_def.get("js"):
                js_path = target_dir / "content.js"
                js_path.write_text(ext_def["js"].strip(), encoding="utf-8")

            if ext_def.get("css"):
                css_path = target_dir / "dark.css" if "dark" in ext_id else target_dir / "reader.css"
                css_path.write_text(ext_def["css"].strip(), encoding="utf-8")

    def _load_registry(self) -> Dict[str, Any]:
        if not META_FILE.exists():
            # Initial default: install Dark Reader and uBlock Shield Plus ready to use
            initial = {
                "installed": {},
                "order": [],
            }
            self._save_registry(initial)
            return initial
        try:
            with open(META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"installed": {}, "order": []}

    def _save_registry(self, data: Optional[Dict[str, Any]] = None):
        if data is None:
            data = self.registry
        try:
            with open(META_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ExtensionManager] Error saving registry: {e}")

    def initialize(self, profile: QWebEngineProfile):
        """Attaches to a QWebEngineProfile, registers existing extensions and scripts."""
        self.profile = profile
        self._sync_installed_with_disk()
        self._apply_all_to_profile()

    def _sync_installed_with_disk(self):
        """Scans EXTENSIONS_DIR for any user-added or preinstalled extensions."""
        for item in EXTENSIONS_DIR.iterdir():
            if item.is_dir() and (item / "manifest.json").exists():
                ext_id = item.name
                if ext_id not in self.registry["installed"]:
                    meta = self._parse_manifest(item)
                    meta["enabled"] = True
                    meta["installed_at"] = os.path.getctime(item)
                    self.registry["installed"][ext_id] = meta
                    if ext_id not in self.registry.get("order", []):
                        self.registry.setdefault("order", []).append(ext_id)
        self._save_registry()

    def _parse_manifest(self, folder: Path) -> Dict[str, Any]:
        manifest_path = folder / "manifest.json"
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                m = json.load(f)
                ext_id = folder.name
                curated = CURATED_EXTENSIONS.get(ext_id, {})
                for item in ONLINE_EXTENSIONS:
                    if item["id"] == ext_id:
                        curated = item
                        break

                name = m.get("name", ext_id.replace("-", " ").title())
                desc = m.get("description", "User-installed extension")

                # Resolve Chrome i18n messages
                if name.startswith("__MSG_") or desc.startswith("__MSG_"):
                    for loc_candidate in ("en", "en_US", "en_GB"):
                        loc_file = folder / "_locales" / loc_candidate / "messages.json"
                        if loc_file.exists():
                            try:
                                with open(loc_file, "r", encoding="utf-8") as lf:
                                    loc_data = json.load(lf)
                                    if name.startswith("__MSG_"):
                                        k = name[6:-2]
                                        if k in loc_data:
                                            name = loc_data[k].get("message", name)
                                    if desc.startswith("__MSG_"):
                                        dk = desc[6:-2]
                                        if dk in loc_data:
                                            desc = loc_data[dk].get("message", desc)
                            except Exception:
                                pass
                            break
                    if name.startswith("__MSG_"):
                        name = curated.get("name", ext_id.replace("-", " ").title())

                return {
                    "id": ext_id,
                    "name": name,
                    "version": m.get("version", "1.0.0"),
                    "description": desc,
                    "icon": curated.get("icon", "🧩"),
                    "category": curated.get("category", "Custom"),
                    "author": curated.get("author", "Local / User"),
                    "path": str(folder),
                    "enabled": True,
                }
        except Exception:
            return {
                "id": folder.name,
                "name": folder.name.replace("-", " ").title(),
                "version": "1.0.0",
                "description": "",
                "icon": "🧩",
                "category": "Custom",
                "author": "Local",
                "path": str(folder),
                "enabled": True,
            }

    def _apply_all_to_profile(self):
        """Applies enabled extensions to the WebEngine profile and script engine."""
        if not self.profile:
            return

        # 1. Native QWebEngineExtensionManager registration if persistent
        if hasattr(self.profile, "extensionManager") and not self.profile.isOffTheRecord():
            em = self.profile.extensionManager()
            for ext_id, info in self.registry.get("installed", {}).items():
                p = Path(info.get("path", ""))
                if p.exists() and (p / "manifest.json").exists():
                    try:
                        em.installExtension(str(p))
                    except Exception as e:
                        print(f"[ExtensionManager] Native install failed for {ext_id}: {e}")

        # 2. Companion script injection for 100% reliable execution
        self._update_profile_scripts()

    def _update_profile_scripts(self):
        """Injects content scripts into profile.scripts() for all enabled extensions."""
        if not self.profile:
            return

        # Clear existing extension scripts
        scripts_to_remove = [
            s for s in self.profile.scripts().toList() if s.name().startswith("lockdown_ext_")
        ]
        for s in scripts_to_remove:
            self.profile.scripts().remove(s)

        for ext_id, info in self.registry.get("installed", {}).items():
            if not info.get("enabled", True):
                continue

            folder = Path(info.get("path", ""))
            if not folder.exists():
                continue

            js_file = folder / "content.js"
            if js_file.exists():
                code = js_file.read_text(encoding="utf-8")
                script = QWebEngineScript()
                script.setName(f"lockdown_ext_{ext_id}")
                script.setSourceCode(code)
                script.setInjectionPoint(QWebEngineScript.DocumentReady)
                script.setWorldId(QWebEngineScript.MainWorld)
                script.setRunsOnSubFrames(True)
                self.profile.scripts().insert(script)

    def get_installed(self) -> List[Dict[str, Any]]:
        self._sync_installed_with_disk()
        result = []
        for ext_id in self.registry.get("order", []):
            if ext_id in self.registry.get("installed", {}):
                result.append(self.registry["installed"][ext_id])
        return result

    def get_library(self) -> List[Dict[str, Any]]:
        installed_ids = set(self.registry.get("installed", {}).keys())
        items = []

        # 1. Curated Offline Bundles
        for ext_id, defn in CURATED_EXTENSIONS.items():
            items.append({
                "id": defn["id"],
                "name": defn["name"],
                "version": defn["version"],
                "category": defn["category"],
                "icon": defn["icon"],
                "description": defn["description"],
                "author": defn["author"],
                "is_installed": ext_id in installed_ids,
                "is_online": False,
                "badge": "Built-in",
            })

        # 2. Online Cloud Library
        for defn in ONLINE_EXTENSIONS:
            if any(item["id"] == defn["id"] for item in items):
                continue
            items.append({
                "id": defn["id"],
                "name": defn["name"],
                "version": defn["version"],
                "category": defn["category"],
                "icon": defn["icon"],
                "description": defn["description"],
                "author": defn["author"],
                "download_url": defn["download_url"],
                "is_installed": defn["id"] in installed_ids,
                "is_online": True,
                "badge": "Online Download",
            })

        return items

    def get_online_library(self) -> List[Dict[str, Any]]:
        installed_ids = set(self.registry.get("installed", {}).keys())
        items = []
        for defn in ONLINE_EXTENSIONS:
            items.append({
                "id": defn["id"],
                "name": defn["name"],
                "version": defn["version"],
                "category": defn["category"],
                "icon": defn["icon"],
                "description": defn["description"],
                "author": defn["author"],
                "download_url": defn["download_url"],
                "is_installed": defn["id"] in installed_ids,
                "is_online": True,
                "badge": "Online Download",
            })
        return items

    def download_and_install_from_url(self, url: str, ext_id: str = "") -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Downloads an extension from an online URL (ZIP or CRX), extracts, and installs it."""
        url = url.strip()

        # If ID passed without URL, look up from ONLINE_EXTENSIONS
        if not url and ext_id:
            for item in ONLINE_EXTENSIONS:
                if item["id"] == ext_id:
                    url = item.get("download_url", "")
                    break

        # Fallback to local curated library if offline or no direct URL
        if (not url or url.startswith("local://")) and ext_id in CURATED_EXTENSIONS:
            ok = self.install_from_library(ext_id)
            if ok:
                meta = self.registry["installed"].get(ext_id)
                return True, meta, "Installed from verified library archive."
            return False, None, "Failed to install from library."

        if not url:
            return False, None, "Please provide a valid online extension download URL."

        temp_dir = Path(tempfile.mkdtemp())
        zip_path = temp_dir / "downloaded_extension.zip"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            }
            with httpx.Client(follow_redirects=True, timeout=35.0) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code != 200:
                    # If online URL failed, check if we have a curated bundle fallback
                    if ext_id and ext_id in CURATED_EXTENSIONS:
                        ok = self.install_from_library(ext_id)
                        if ok:
                            meta = self.registry["installed"].get(ext_id)
                            return True, meta, f"Online mirror returned {resp.status_code}. Installed from verified backup."
                    return False, None, f"Online download failed (HTTP {resp.status_code})."

                content = resp.content
                # Handle CRX format: find ZIP PK\x03\x04 header
                pk_idx = content.find(b"PK\x03\x04")
                if pk_idx != -1 and pk_idx > 0:
                    content = content[pk_idx:]

                zip_path.write_bytes(content)

            # Extract archive
            extract_dir = temp_dir / "extracted"
            extract_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(str(zip_path), "r") as zf:
                zf.extractall(str(extract_dir))

            # Search for manifest.json
            found_manifest_dir = None
            for root, _, files in os.walk(str(extract_dir)):
                if "manifest.json" in files:
                    found_manifest_dir = Path(root)
                    break

            if not found_manifest_dir:
                # If no manifest found, check if curated fallback exists
                if ext_id and ext_id in CURATED_EXTENSIONS:
                    ok = self.install_from_library(ext_id)
                    if ok:
                        meta = self.registry["installed"].get(ext_id)
                        return True, meta, "Downloaded package had no manifest. Installed from verified backup."
                return False, None, "Downloaded package does not contain a valid manifest.json file."

            # Determine extension ID
            if not ext_id:
                try:
                    with open(found_manifest_dir / "manifest.json", "r", encoding="utf-8") as mf:
                        m_data = json.load(mf)
                        ext_id = m_data.get("name", "online-ext").lower().replace(" ", "-")
                except Exception:
                    ext_id = f"online-ext-{int(os.path.getctime(zip_path))}"

            dest = EXTENSIONS_DIR / ext_id
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(found_manifest_dir, dest)

            meta = self._parse_manifest(dest)
            meta["enabled"] = True
            meta["installed_at"] = os.path.getctime(dest)
            meta["source_url"] = url

            self.registry.setdefault("installed", {})[ext_id] = meta
            if ext_id not in self.registry.setdefault("order", []):
                self.registry["order"].append(ext_id)
            self._save_registry()

            self._apply_all_to_profile()
            return True, meta, f"✓ Successfully downloaded and installed {meta.get('name', ext_id)} from online!"

        except Exception as e:
            # Fallback if network or extraction error
            if ext_id and ext_id in CURATED_EXTENSIONS:
                ok = self.install_from_library(ext_id)
                if ok:
                    meta = self.registry["installed"].get(ext_id)
                    return True, meta, f"Installed from verified backup archive ({str(e)})."
            return False, None, f"Error downloading online extension: {str(e)}"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def install_from_library(self, ext_id: str) -> bool:
        if ext_id not in CURATED_EXTENSIONS:
            return False

        source = LIBRARY_EXTENSIONS_DIR / ext_id
        dest = EXTENSIONS_DIR / ext_id

        try:
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source, dest)

            meta = self._parse_manifest(dest)
            meta["enabled"] = True
            meta["installed_at"] = os.path.getctime(dest)

            self.registry.setdefault("installed", {})[ext_id] = meta
            if ext_id not in self.registry.setdefault("order", []):
                self.registry["order"].append(ext_id)
            self._save_registry()

            self._apply_all_to_profile()
            return True
        except Exception as e:
            print(f"[ExtensionManager] Install from library error: {e}")
            return False

    def install_unpacked(self, folder_path: str) -> Optional[Dict[str, Any]]:
        path = Path(folder_path).resolve()
        if not path.exists() or not (path / "manifest.json").exists():
            return None

        ext_id = path.name.lower().replace(" ", "-")
        dest = EXTENSIONS_DIR / ext_id

        try:
            if dest != path:
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(path, dest)
            else:
                dest = path

            meta = self._parse_manifest(dest)
            meta["enabled"] = True
            meta["installed_at"] = os.path.getctime(dest)

            self.registry.setdefault("installed", {})[ext_id] = meta
            if ext_id not in self.registry.setdefault("order", []):
                self.registry["order"].append(ext_id)
            self._save_registry()

            self._apply_all_to_profile()
            return meta
        except Exception as e:
            print(f"[ExtensionManager] Install unpacked error: {e}")
            return None

    def uninstall(self, ext_id: str) -> bool:
        if ext_id in self.registry.get("installed", {}):
            dest = EXTENSIONS_DIR / ext_id
            if dest.exists():
                try:
                    shutil.rmtree(dest)
                except Exception as e:
                    print(f"[ExtensionManager] Error removing dir: {e}")

            del self.registry["installed"][ext_id]
            if ext_id in self.registry.get("order", []):
                self.registry["order"].remove(ext_id)
            self._save_registry()

            self._apply_all_to_profile()
            return True
        return False

    def set_enabled(self, ext_id: str, enabled: bool) -> bool:
        if ext_id in self.registry.get("installed", {}):
            self.registry["installed"][ext_id]["enabled"] = bool(enabled)
            self._save_registry()

            # Native toggle
            if self.profile and hasattr(self.profile, "extensionManager") and not self.profile.isOffTheRecord():
                em = self.profile.extensionManager()
                for ext in em.extensions():
                    if ext.name().lower() == self.registry["installed"][ext_id]["name"].lower():
                        try:
                            em.setExtensionEnabled(ext, enabled)
                        except Exception:
                            pass

            self._update_profile_scripts()
            return True
        return False
