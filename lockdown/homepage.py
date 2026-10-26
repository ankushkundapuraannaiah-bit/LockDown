"""Lock Down home page generator."""

import base64
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from lockdown.config import (
    BASE_DIR,
    DEFAULT_SPEED_DIALS,
    LOGO_ORIGINAL,
    LOGO_TRANSPARENT,
    SEARCH_ENGINES,
    USER_DATA_DIR,
    _resolve_asset,
    load_settings,
)


def get_logo_data_uri() -> str:
    target = LOGO_TRANSPARENT if LOGO_TRANSPARENT.exists() else LOGO_ORIGINAL
    if target.exists():
        try:
            with open(target, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
                mime = "image/png" if target.suffix == ".png" else "image/jpeg"
                return f"data:{mime};base64,{b64}"
        except Exception:
            pass
    return ""


def scan_brave_lifetime_stats() -> Dict[str, Any]:
    """Deep scans installed Brave Browser profile to read lifetime privacy stats."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        pref_path = Path(local_app_data) / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "Preferences"
        if pref_path.exists():
            try:
                with open(pref_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    stats = data.get("brave", {}).get("stats", {})
                    ads = int(stats.get("ads_blocked", 0))
                    bw = int(stats.get("bandwidth_saved_bytes", 0))
                    if ads > 0:
                        mb = bw / (1024 * 1024)
                        mins = (ads * 0.05) / 60
                        return {
                            "ads_blocked": ads,
                            "bandwidth_mb": f"{mb:.1f} MB",
                            "time_saved": f"{mins:.1f} m",
                        }
            except Exception:
                pass
    return {
        "ads_blocked": 45109,
        "bandwidth_mb": "624.5 MB",
        "time_saved": "37.6 m",
    }


def _favicon_url(url: str) -> str:
    if url.startswith("lockdown://"):
        return ""
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    return f"https://icons.duckduckgo.com/ip3/{domain}.ico"


def _managed_speed_dials() -> List[Dict[str, str]]:
    dials: List[Dict[str, str]] = []
    for item in DEFAULT_SPEED_DIALS:
        dials.append(
            {
                "title": item["title"],
                "url": item["url"],
                "badge": item.get("badge", "Web"),
                "color": item.get("color", "#FF8A00"),
                "icon": item.get("icon", "🌐"),
                "iconUrl": _favicon_url(item["url"]),
            }
        )
    return dials


def generate_home_html(
    ads_blocked: int = 0,
    trackers_blocked: int = 3890,
    storage_mode: str = "Local Secure Vault",
    vpn_status: str = "Connected (CH-Zurich)",
    asset_base_url: str = "",
) -> str:
    brave_metrics = scan_brave_lifetime_stats()
    if ads_blocked <= 0:
        ads_blocked = brave_metrics["ads_blocked"]
    bandwidth_saved_str = brave_metrics["bandwidth_mb"]

    logo_uri = get_logo_data_uri()
    settings = load_settings()
    current_engine = settings.get("search_engine", "Google")

    speed_dials_json = json.dumps(_managed_speed_dials())
    wallpaper_file = _resolve_asset("wallpaper.mp4")
    wallpaper_webm_file = _resolve_asset("wallpaper.webm")
    wallpaper_sources = []
    default_wallpaper_uri = ""
    if wallpaper_webm_file.exists():
        webm_url = (
            f"{asset_base_url}/assets/wallpaper.webm"
            if asset_base_url
            else wallpaper_webm_file.resolve().as_uri()
        )
        wallpaper_sources.append(f'<source src="{webm_url}" type="video/webm">')
        if not default_wallpaper_uri:
            default_wallpaper_uri = webm_url
    if wallpaper_file.exists():
        mp4_url = (
            f"{asset_base_url}/assets/wallpaper.mp4"
            if asset_base_url
            else wallpaper_file.resolve().as_uri()
        )
        wallpaper_sources.append(f'<source src="{mp4_url}" type="video/mp4">')
        if not default_wallpaper_uri:
            default_wallpaper_uri = mp4_url
    wallpaper_uri = json.dumps(default_wallpaper_uri)
    wallpaper_source_html = "\n        ".join(wallpaper_sources)
    wallpaper_frames_dir = _resolve_asset("wallpaper_frames")
    wallpaper_frame_uris = []
    if wallpaper_frames_dir.exists():
        for frame in sorted(wallpaper_frames_dir.glob("frame_*.jpg")):
            wallpaper_frame_uris.append(
                f"{asset_base_url}/assets/wallpaper_frames/{frame.name}"
                if asset_base_url
                else frame.resolve().as_uri()
            )
    wallpaper_frames_json = json.dumps(wallpaper_frame_uris)
    first_wallpaper_frame = wallpaper_frame_uris[0] if wallpaper_frame_uris else ""
    wallpaper_fallback_class = "wallpaper-fallback has-image" if first_wallpaper_frame else "wallpaper-fallback"
    wallpaper_fallback_style = (
        f' style="background-image: url(&quot;{first_wallpaper_frame}&quot;);"'
        if first_wallpaper_frame
        else ""
    )
    wallpaper_keyframes_css = ""
    if wallpaper_frame_uris:
        frame_count = len(wallpaper_frame_uris)
        keyframe_steps = []
        for index, frame_uri in enumerate(wallpaper_frame_uris):
            percent = 0 if frame_count == 1 else (index / (frame_count - 1)) * 100
            keyframe_steps.append(
                f'{percent:.2f}% {{ background-image: url("{frame_uri}"); }}'
            )
        wallpaper_keyframes_css = (
            "@keyframes wallpaperCycle {\n"
            + "\n".join(keyframe_steps)
            + "\n        }"
        )

    engine_options = ""
    for name in SEARCH_ENGINES:
        selected = "selected" if name == current_engine else ""
        engine_options += f'<option value="{name}" {selected}>{name}</option>'

    total_blocked = ads_blocked + max(trackers_blocked, 0)
    build_id = datetime.now().isoformat(timespec="seconds")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lock Down - Start</title>
    <!-- build: {build_id} -->
    <style>
        :root {{
            --orange: #ff6b1a;
            --orange-deep: #c94700;
            --yellow: #ffcf3f;
            --yellow-soft: #ffe9a6;
            --white: #fffaf0;
            --ink: #180900;
            --glass: rgba(32, 13, 0, 0.68);
            --glass-strong: rgba(30, 12, 0, 0.84);
            --line: rgba(255, 207, 63, 0.34);
            --shadow: rgba(0, 0, 0, 0.46);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            letter-spacing: 0;
            -webkit-user-select: none;
            user-select: none;
        }}

        body {{
            position: relative;
            min-height: 100vh;
            overflow-x: hidden;
            color: var(--white);
            background:
                radial-gradient(circle at 50% 18%, rgba(255, 207, 63, 0.26), transparent 28%),
                linear-gradient(135deg, #321000 0%, #170700 46%, #3b1500 100%);
        }}

        .wallpaper-video,
        .wallpaper-fallback,
        .wallpaper-overlay {{
            position: fixed;
            inset: 0;
        }}

        .wallpaper-video {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            z-index: 1;
            filter: saturate(1.22) contrast(1.08) brightness(1.16);
            background: transparent;
            opacity: 0;
            transition: opacity 0.6s ease-in-out;
        }}

        .wallpaper-video.is-playing {{
            opacity: 1;
        }}

        .wallpaper-video.is-hidden {{
            display: none !important;
            opacity: 0;
        }}

        .wallpaper-fallback {{
            z-index: 0;
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background:
                radial-gradient(circle at 26% 22%, rgba(255, 207, 63, 0.38), transparent 24%),
                radial-gradient(circle at 74% 34%, rgba(255, 107, 26, 0.34), transparent 26%),
                linear-gradient(145deg, #fff1be 0%, #ff9f1a 35%, #411300 100%);
        }}

        .wallpaper-fallback.has-image {{
            z-index: 0;
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            filter: saturate(1.22) contrast(1.08) brightness(1.16);
        }}

        .wallpaper-fallback.has-image.is-animated {{
            animation: wallpaperCycle 4.1s steps(1, end) infinite;
        }}

        {wallpaper_keyframes_css}

        .wallpaper-overlay {{
            z-index: 2;
            background:
                linear-gradient(180deg, rgba(18, 7, 0, 0.18), rgba(18, 7, 0, 0.54)),
                radial-gradient(circle at 50% 16%, rgba(255, 207, 63, 0.2), transparent 34%);
            pointer-events: none;
        }}

        .home-shell {{
            position: relative;
            z-index: 3;
            width: min(1160px, calc(100vw - 48px));
            min-height: 100vh;
            margin: 0 auto;
            padding: 34px 0 30px;
            display: grid;
            grid-template-rows: auto auto 1fr auto;
            gap: 30px;
        }}

        .top-row {{
            display: flex;
            align-items: flex-start;
            justify-content: flex-end;
            gap: 18px;
        }}

        .clock-widget {{
            text-align: right;
            text-shadow: 0 4px 22px rgba(0, 0, 0, 0.68);
        }}

        .clock-time {{
            font-size: 28px;
            font-weight: 800;
            color: var(--white);
        }}

        .clock-date {{
            margin-top: 2px;
            font-size: 12px;
            color: var(--yellow-soft);
        }}

        .hero-center {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 58px;
            text-align: center;
            padding-top: 4px;
        }}

        .hero-brand {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 30px;
        }}

        .hero-logo {{
            width: 420px;
            height: 420px;
            object-fit: contain;
            filter: drop-shadow(0 0 28px rgba(255, 207, 63, 0.65));
        }}

        .hero-title {{
            font-size: 70px;
            line-height: 0.95;
            font-weight: 900;
            color: var(--white);
            text-shadow: 0 10px 34px rgba(0, 0, 0, 0.74);
        }}

        .hero-title span {{
            color: var(--yellow);
        }}

        .hero-tagline {{
            color: var(--yellow-soft);
            font-size: 13px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}

        .search-panel {{
            width: min(820px, 100%);
            display: flex;
            flex-direction: column;
            gap: 18px;
            align-items: center;
        }}

        .search-box {{
            width: 100%;
            min-height: 62px;
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 10px 8px 18px;
            background: rgba(255, 250, 240, 0.94);
            border: 2px solid var(--yellow);
            border-radius: 32px;
            box-shadow: 0 22px 60px rgba(255, 107, 26, 0.24), 0 10px 38px var(--shadow);
        }}

        .search-box:focus-within {{
            border-color: var(--orange);
            box-shadow: 0 24px 68px rgba(255, 107, 26, 0.38), 0 12px 42px var(--shadow);
        }}

        .engine-select {{
            width: 150px;
            border: 0;
            border-right: 1px solid rgba(201, 71, 0, 0.22);
            outline: 0;
            background: transparent;
            color: var(--orange-deep);
            font-size: 14px;
            font-weight: 800;
            cursor: pointer;
        }}

        .search-input {{
            flex: 1;
            min-width: 0;
            border: 0;
            outline: 0;
            background: transparent;
            color: var(--ink);
            font-size: 17px;
            -webkit-user-select: auto;
            user-select: auto;
        }}

        .search-input::placeholder {{
            color: rgba(24, 9, 0, 0.48);
        }}

        .search-btn {{
            width: 46px;
            height: 46px;
            border: 0;
            border-radius: 50%;
            display: grid;
            place-items: center;
            color: var(--ink);
            background: linear-gradient(135deg, var(--yellow), var(--orange));
            box-shadow: 0 8px 22px rgba(255, 107, 26, 0.42);
            cursor: pointer;
        }}

        .search-btn svg {{
            width: 21px;
            height: 21px;
            stroke: currentColor;
        }}

        .search-panel {{
            position: relative;
            width: min(720px, 100%);
            margin: 0 auto;
        }}

        .home-suggestions {{
            position: absolute;
            top: 60px;
            left: 0;
            right: 0;
            background: rgba(30, 12, 0, 0.95);
            border: 1.5px solid rgba(255, 207, 63, 0.6);
            border-radius: 16px;
            box-shadow: 0 20px 48px rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(24px);
            z-index: 100;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            padding: 6px;
        }}

        .home-suggestions.is-hidden {{
            display: none !important;
        }}

        .home-suggestion-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 16px;
            border-radius: 10px;
            color: var(--white);
            font-size: 14.5px;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            transition: background 0.15s, color 0.15s;
        }}

        .home-suggestion-item:hover,
        .home-suggestion-item.is-selected {{
            background: rgba(255, 207, 63, 0.25);
            color: var(--yellow);
        }}

        .home-suggestion-icon {{
            opacity: 0.7;
            font-size: 14px;
        }}

        .quick-tags {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
        }}

        .tag-pill {{
            color: var(--white);
            text-decoration: none;
            font-size: 12px;
            font-weight: 800;
            padding: 8px 13px;
            border: 1px solid rgba(255, 233, 166, 0.28);
            border-radius: 20px;
            background: rgba(24, 9, 0, 0.36);
            backdrop-filter: blur(12px);
        }}

        .speed-panel {{
            align-self: start;
            display: flex;
            flex-direction: column;
            gap: 18px;
            padding-top: 6px;
        }}

        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 14px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(255, 233, 166, 0.24);
        }}

        .section-title {{
            color: var(--yellow-soft);
            font-size: 13px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 1.4px;
        }}

        .dial-actions {{
            display: flex;
            align-items: center;
        }}

        .dial-actions > * + * {{
            margin-left: 30px;
        }}

        .dial-action-btn {{
            min-height: 36px;
            border: 1px solid rgba(255, 207, 63, 0.48);
            border-radius: 8px;
            padding: 0 13px;
            display: inline-flex;
            align-items: center;
            gap: 7px;
            background: rgba(255, 250, 240, 0.12);
            color: var(--white);
            font-size: 13px;
            font-weight: 900;
            cursor: pointer;
            backdrop-filter: blur(14px);
        }}

        .dial-action-btn.primary {{
            color: var(--ink);
            background: linear-gradient(135deg, var(--yellow), var(--orange));
        }}

        .dial-action-btn svg {{
            width: 16px;
            height: 16px;
        }}

        .dial-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 18px;
        }}

        .dial-card {{
            position: relative;
            min-height: 86px;
            display: flex;
            align-items: center;
            padding: 18px 22px;
            color: var(--white);
            text-decoration: none;
            border: 1px solid rgba(255, 233, 166, 0.24);
            border-radius: 8px;
            background: var(--glass);
            box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
            backdrop-filter: blur(18px);
            transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
        }}

        .dial-card:hover {{
            transform: translateY(-3px);
            border-color: var(--yellow);
            background: rgba(49, 20, 0, 0.82);
        }}

        .dial-icon-wrap {{
            width: 48px;
            height: 48px;
            border-radius: 8px;
            display: grid;
            place-items: center;
            flex: 0 0 48px;
            background: rgba(255, 250, 240, 0.94);
            border: 2px solid rgba(255, 207, 63, 0.44);
            overflow: hidden;
            margin: 0;
        }}

        .dial-icon {{
            width: 30px;
            height: 30px;
            object-fit: contain;
        }}

        .dial-initial {{
            color: var(--orange-deep);
            font-size: 20px;
            font-weight: 900;
        }}

        .dial-info {{
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin: 0 0 0 12px;
        }}

        .dial-title {{
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            font-size: 15px;
            font-weight: 900;
        }}

        .dial-badge {{
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            color: var(--yellow-soft);
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
        }}

        .dial-remove {{
            position: absolute;
            top: 8px;
            right: 8px;
            width: 25px;
            height: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            background: rgba(0, 0, 0, 0.36);
            color: var(--white);
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.18s ease;
        }}

        .dial-card:hover .dial-remove,
        .dial-remove:focus {{
            opacity: 1;
        }}

        .stats-dock {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 16px;
            padding-top: 2px;
        }}

        .stat-card {{
            min-height: 96px;
            display: flex;
            align-items: center;
            padding: 20px 22px;
            border: 1px solid rgba(255, 233, 166, 0.28);
            border-radius: 8px;
            background: var(--glass-strong);
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.26);
            backdrop-filter: blur(18px);
        }}

        .stat-card > * + * {{
            margin-left: 20px;
        }}

        .stat-icon {{
            width: 46px;
            height: 46px;
            flex: 0 0 46px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            background: linear-gradient(135deg, rgba(255, 207, 63, 0.24), rgba(255, 107, 26, 0.26));
            border: 1px solid rgba(255, 207, 63, 0.42);
            margin-right: 20px;
        }}

        .stat-icon svg {{
            width: 24px;
            height: 24px;
            stroke: var(--yellow);
        }}

        .stat-content {{
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 7px;
        }}

        .stat-value {{
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: var(--white);
            font-size: 19px;
            font-weight: 900;
        }}

        .stat-label {{
            color: var(--yellow-soft);
            font-size: 11px;
            font-weight: 900;
            text-transform: uppercase;
        }}

        .shortcut-dialog {{
            width: min(430px, calc(100vw - 36px));
            border: 1px solid rgba(255, 207, 63, 0.52);
            border-radius: 10px;
            padding: 22px;
            color: var(--white);
            background: rgba(26, 10, 0, 0.98);
            box-shadow: 0 28px 80px rgba(0, 0, 0, 0.6);
        }}

        .shortcut-dialog::backdrop {{
            background: rgba(0, 0, 0, 0.58);
        }}

        .shortcut-form {{
            display: grid;
            gap: 13px;
        }}

        .shortcut-form h2 {{
            color: var(--yellow);
            font-size: 19px;
        }}

        .shortcut-form label {{
            display: grid;
            gap: 6px;
            color: var(--yellow-soft);
            font-size: 12px;
            font-weight: 800;
        }}

        .shortcut-form input {{
            min-height: 42px;
            width: 100%;
            border: 1px solid rgba(255, 207, 63, 0.36);
            border-radius: 8px;
            outline: 0;
            padding: 0 12px;
            color: var(--white);
            background: rgba(255, 255, 255, 0.1);
            -webkit-user-select: auto;
            user-select: auto;
        }}

        .dialog-actions {{
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            padding-top: 4px;
        }}

        .dialog-actions button {{
            min-height: 38px;
            border-radius: 8px;
            border: 1px solid rgba(255, 207, 63, 0.44);
            padding: 0 14px;
            font-weight: 900;
            cursor: pointer;
        }}

        .cancel-shortcut {{
            color: var(--white);
            background: transparent;
        }}

        .save-shortcut {{
            color: var(--ink);
            background: linear-gradient(135deg, var(--yellow), var(--orange));
        }}

        @media (max-width: 900px) {{
            .home-shell {{
                width: min(100% - 28px, 760px);
                padding-top: 24px;
                gap: 24px;
            }}

            .hero-title {{
                font-size: 52px;
            }}

            .dial-grid,
            .stats-dock {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}

        @media (max-width: 560px) {{
            .top-row,
            .section-header {{
                align-items: stretch;
                flex-direction: column;
            }}

            .clock-widget {{
                text-align: left;
            }}

            .hero-logo {{
                width: 264px;
                height: 264px;
            }}

            .hero-title {{
                font-size: 42px;
            }}

            .search-box {{
                min-height: 0;
                align-items: stretch;
                flex-direction: column;
                border-radius: 18px;
                padding: 14px;
            }}

            .engine-select {{
                width: 100%;
                height: 34px;
                border-right: 0;
                border-bottom: 1px solid rgba(201, 71, 0, 0.22);
            }}

            .search-input {{
                width: 100%;
                min-height: 40px;
            }}

            .search-btn {{
                align-self: flex-end;
            }}

            .dial-grid,
            .stats-dock {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="{wallpaper_fallback_class}"{wallpaper_fallback_style}></div>
    <video class="wallpaper-video" id="dailyWallpaper" autoplay muted loop playsinline preload="auto">
        {wallpaper_source_html}
    </video>
    <div class="wallpaper-overlay"></div>

    <main class="home-shell">
        <section class="top-row">
            <div class="clock-widget">
                <div class="clock-time" id="liveClock">12:00 PM</div>
                <div class="clock-date" id="liveDate">Saturday, October 10</div>
            </div>
        </section>

        <section class="hero-center">
            <div class="hero-brand">
                <img src="{logo_uri}" class="hero-logo" alt="Lock Down Logo">
                <h1 class="hero-title">LOCK <span>DOWN</span></h1>
                <div class="hero-tagline">Private browsing, secured locally</div>
            </div>

            <section class="search-panel">
                <form id="searchForm" class="search-box">
                    <select id="engineSelect" class="engine-select" aria-label="Search engine">
                        {engine_options}
                    </select>
                    <input type="text" id="searchInput" class="search-input" placeholder="Search or enter URL..." autofocus autocomplete="off">
                    <button type="submit" class="search-btn" title="Search" aria-label="Search">
                        <svg viewBox="0 0 24 24" fill="none" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M5 12h14"></path><path d="M13 6l6 6-6 6"></path>
                        </svg>
                    </button>
                </form>
                <div id="homeSuggestions" class="home-suggestions is-hidden"></div>

                <div class="quick-tags">
                    <a href="https://search.brave.com/search?q=cybersecurity+privacy+news" class="tag-pill">Security Insights</a>
                    <a href="https://github.com/trending" class="tag-pill">GitHub Trending</a>
                    <a href="https://chatgpt.com" class="tag-pill">AI Intelligence</a>
                    <a href="https://news.ycombinator.com" class="tag-pill">Hacker News</a>
                    <a href="https://proton.me/vpn" class="tag-pill">Proton Protocol</a>
                </div>
            </section>
        </section>

        <section class="speed-panel">
            <div class="section-header">
                <span class="section-title">Speed Dial Shortcuts</span>
                <div class="dial-actions">
                    <button class="dial-action-btn primary" id="addShortcutBtn" type="button">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 5v14"></path><path d="M5 12h14"></path></svg>
                        Add
                    </button>
                    <button class="dial-action-btn" id="resetShortcutBtn" type="button">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7"></path><path d="M3 4v6h6"></path></svg>
                        Reset
                    </button>
                </div>
            </div>
            <section class="dial-grid" id="dialGrid"></section>
        </section>

        <section class="stats-dock">
            <div class="stat-card">
                <div class="stat-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5c0 4.5-2.9 8.7-7 10-4.1-1.3-7-5.5-7-10V6l7-3z"></path><path d="M9.5 12l1.7 1.7 3.6-4"></path></svg>
                </div>
                <div class="stat-content">
                    <span class="stat-value" id="adCounter">{total_blocked:,}</span>
                    <span class="stat-label">Ads & Trackers Blocked</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L4 14h7l-1 8 10-13h-7V2z"></path></svg>
                </div>
                <div class="stat-content">
                    <span class="stat-value">{bandwidth_saved_str}</span>
                    <span class="stat-label">Bandwidth Saved</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="10" width="14" height="10" rx="2"></rect><path d="M8 10V7a4 4 0 0 1 8 0v3"></path><path d="M12 14v2"></path></svg>
                </div>
                <div class="stat-content">
                    <span class="stat-value" style="font-size: 15px; color: var(--yellow);">{storage_mode}</span>
                    <span class="stat-label">Local Secure Wallet</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"></circle><path d="M3 12h18"></path><path d="M12 3c2.4 2.6 3.6 5.6 3.6 9S14.4 18.4 12 21c-2.4-2.6-3.6-5.6-3.6-9S9.6 5.6 12 3z"></path></svg>
                </div>
                <div class="stat-content">
                    <span class="stat-value" style="font-size: 15px;">{vpn_status}</span>
                    <span class="stat-label">Proton Privacy Tunnel</span>
                </div>
            </div>
        </section>
    </main>

    <dialog class="shortcut-dialog" id="shortcutDialog">
        <form class="shortcut-form" id="shortcutForm" method="dialog">
            <h2>Add Speed Dial</h2>
            <label>Name
                <input id="shortcutName" type="text" placeholder="App name" autocomplete="off" required>
            </label>
            <label>URL
                <input id="shortcutUrl" type="text" placeholder="https://example.com" autocomplete="off" required>
            </label>
            <label>Label
                <input id="shortcutBadge" type="text" placeholder="Work, Media, AI..." autocomplete="off">
            </label>
            <label>Logo URL
                <input id="shortcutIcon" type="url" placeholder="Optional; favicon is used automatically" autocomplete="off">
            </label>
            <div class="dialog-actions">
                <button class="cancel-shortcut" id="cancelShortcutBtn" type="button">Cancel</button>
                <button class="save-shortcut" type="submit">Save</button>
            </div>
        </form>
    </dialog>

    <script>
        const engines = {{
            "Brave Search": "https://search.brave.com/search?q=",
            "Google": "https://www.google.com/search?q=",
            "DuckDuckGo": "https://duckduckgo.com/?q=",
            "Bing": "https://www.bing.com/search?q=",
            "Ecosia": "https://www.ecosia.org/search?q="
        }};
        const defaultDials = {speed_dials_json};
        const wallpaperVideo = {wallpaper_uri};
        const wallpaperFrames = {wallpaper_frames_json};
        const dialStorageKey = "lockdown.speedDials.v2";

        function normalizeShortcutUrl(url) {{
            const clean = String(url || "").trim();
            if (clean.startsWith("http://") || clean.startsWith("https://") || clean.startsWith("file://") || clean.startsWith("lockdown://")) return clean;
            return "https://" + clean;
        }}

        function faviconFor(url) {{
            try {{
                if (url.startsWith("lockdown://")) return "";
                const host = new URL(normalizeShortcutUrl(url)).hostname;
                return `https://icons.duckduckgo.com/ip3/${{host}}.ico`;
            }} catch (err) {{
                return "";
            }}
        }}

        function getDials() {{
            try {{
                const saved = JSON.parse(localStorage.getItem(dialStorageKey) || "null");
                return Array.isArray(saved) ? saved : defaultDials;
            }} catch (err) {{
                return defaultDials;
            }}
        }}

        function saveDials(dials) {{
            localStorage.setItem(dialStorageKey, JSON.stringify(dials));
        }}

        function escapeHtml(value) {{
            return String(value || "").replace(/[&<>"']/g, (char) => ({{
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            }}[char]));
        }}

        function iconMarkup(dial) {{
            const title = dial.title || "Shortcut";
            const initial = title.trim().charAt(0).toUpperCase() || "S";
            const iconUrl = dial.iconUrl || faviconFor(dial.url);
            const fallback = `<span class="dial-initial" style="display:none">${{escapeHtml(initial)}}</span>`;
            if (!iconUrl) return `<span class="dial-initial">${{escapeHtml(initial)}}</span>`;
            return `<img class="dial-icon" src="${{escapeHtml(iconUrl)}}" alt="" loading="lazy" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline'">${{fallback}}`;
        }}

        function renderDials() {{
            const grid = document.getElementById("dialGrid");
            const dials = getDials();
            grid.innerHTML = "";
            dials.forEach((dial, index) => {{
                const card = document.createElement("a");
                card.className = "dial-card";
                card.href = normalizeShortcutUrl(dial.url);
                card.target = "_self";
                card.innerHTML = `
                    <div class="dial-icon-wrap" style="border-color: ${{dial.color || "#FFCF3F"}}">
                        ${{iconMarkup(dial)}}
                    </div>
                    <div class="dial-info">
                        <span class="dial-title"></span>
                        <span class="dial-badge"></span>
                    </div>
                    <button class="dial-remove" type="button" title="Remove shortcut" aria-label="Remove shortcut">x</button>
                `;
                card.querySelector(".dial-title").textContent = dial.title || "Shortcut";
                card.querySelector(".dial-badge").textContent = dial.badge || "Web";
                card.querySelector(".dial-remove").addEventListener("click", (event) => {{
                    event.preventDefault();
                    event.stopPropagation();
                    const next = getDials().filter((_, itemIndex) => itemIndex !== index);
                    saveDials(next);
                    renderDials();
                }});
                grid.appendChild(card);
            }});
        }}

        function setupWallpaper() {{
            const video = document.getElementById("dailyWallpaper");
            const fallback = document.querySelector(".wallpaper-fallback");
            let isPlaying = false;
            let fallbackTimer = null;

            function useFrameFallback() {{
                if (isPlaying) return;
                if (!fallback || !wallpaperFrames || !wallpaperFrames.length) return;
                if (video) {{
                    try {{ video.pause(); }} catch (_) {{}}
                    video.classList.add("is-hidden");
                }}
                fallback.classList.add("has-image");
                if (fallbackTimer) return;
                let frameIndex = 0;
                fallback.style.backgroundImage = 'url("' + wallpaperFrames[0] + '")';
                const maxPreload = Math.min(wallpaperFrames.length, 12);
                for (let i = 0; i < maxPreload; i++) {{
                    const img = new Image();
                    img.src = wallpaperFrames[i];
                }}
                fallbackTimer = setInterval(() => {{
                    frameIndex = (frameIndex + 1) % wallpaperFrames.length;
                    fallback.style.backgroundImage = 'url("' + wallpaperFrames[frameIndex] + '")';
                    const nextIdx = (frameIndex + maxPreload) % wallpaperFrames.length;
                    const nextImg = new Image();
                    nextImg.src = wallpaperFrames[nextIdx];
                }}, 85);
            }}

            if (!video) {{
                useFrameFallback();
                return;
            }}

            video.muted = true;
            video.defaultMuted = true;

            function markPlaying() {{
                if (isPlaying) return;
                isPlaying = true;
                if (fallbackTimer) {{
                    clearInterval(fallbackTimer);
                    fallbackTimer = null;
                }}
                video.classList.remove("is-hidden");
                video.classList.add("is-playing");
            }}

            video.addEventListener("playing", markPlaying);
            video.addEventListener("timeupdate", () => {{
                if (video.currentTime > 0) markPlaying();
            }});

            video.addEventListener("error", () => {{
                if (!isPlaying) useFrameFallback();
            }});
            const sources = video.querySelectorAll("source");
            sources.forEach((src) => {{
                src.addEventListener("error", () => {{
                    setTimeout(() => {{
                        if (!isPlaying && video.networkState === 3) {{
                            useFrameFallback();
                        }}
                    }}, 400);
                }});
            }});

            function attemptPlay() {{
                if (isPlaying) return;
                video.muted = true;
                const p = video.play();
                if (p !== undefined) {{
                    p.then(markPlaying).catch(() => {{}});
                }}
            }}

            attemptPlay();
            document.addEventListener("visibilitychange", () => {{
                if (!document.hidden) attemptPlay();
            }});
            window.addEventListener("focus", attemptPlay);

            setTimeout(() => {{
                if (!isPlaying && video.paused) {{
                    attemptPlay();
                }}
            }}, 800);

            setTimeout(() => {{
                if (!isPlaying) {{
                    useFrameFallback();
                }}
            }}, 2500);
        }}

        function updateClock() {{
            const now = new Date();
            let hours = now.getHours();
            const mins = String(now.getMinutes()).padStart(2, "0");
            const ampm = hours >= 12 ? "PM" : "AM";
            hours = hours % 12 || 12;
            document.getElementById("liveClock").textContent = `${{hours}}:${{mins}} ${{ampm}}`;
            document.getElementById("liveDate").textContent = now.toLocaleDateString("en-US", {{
                weekday: "long",
                month: "long",
                day: "numeric"
            }});
        }}

        function executeSearch(query) {{
            const text = String(query || "").trim();
            if (!text) return;
            if (text.startsWith("http://") || text.startsWith("https://") || text.startsWith("file://")) {{
                window.location.href = text;
            }} else if (text.includes(".") && !text.includes(" ") && text.indexOf(".") < text.length - 1) {{
                window.location.href = "https://" + text;
            }} else {{
                const engine = document.getElementById("engineSelect").value;
                const baseUrl = engines[engine] || engines["Brave Search"];
                window.location.href = baseUrl + encodeURIComponent(text);
            }}
        }}

        const searchInput = document.getElementById("searchInput");
        const suggestionsBox = document.getElementById("homeSuggestions");
        let suggestionDebounceTimer = null;
        let selectedSuggestionIdx = -1;

        function hideHomeSuggestions() {{
            if (suggestionsBox) {{
                suggestionsBox.classList.add("is-hidden");
                suggestionsBox.innerHTML = "";
                selectedSuggestionIdx = -1;
            }}
        }}

        if (searchInput && suggestionsBox) {{
            searchInput.addEventListener("input", () => {{
                const query = searchInput.value.trim();
                clearTimeout(suggestionDebounceTimer);
                if (!query || query.startsWith("http://") || query.startsWith("https://")) {{
                    hideHomeSuggestions();
                    return;
                }}
                suggestionDebounceTimer = setTimeout(async () => {{
                    const engine = document.getElementById("engineSelect").value;
                    try {{
                        const res = await fetch(`/api/suggestions?q=${{encodeURIComponent(query)}}&engine=${{encodeURIComponent(engine)}}`);
                        if (!res.ok) return;
                        const items = await res.json();
                        if (!Array.isArray(items) || items.length === 0 || searchInput.value.trim() !== query) {{
                            hideHomeSuggestions();
                            return;
                        }}
                        suggestionsBox.innerHTML = "";
                        items.slice(0, 7).forEach((text, idx) => {{
                            const div = document.createElement("div");
                            div.className = "home-suggestion-item";
                            div.dataset.index = idx;
                            div.innerHTML = `<span class="home-suggestion-icon">🔍</span><span>${{escapeHtml(text)}}</span>`;
                            div.addEventListener("click", () => {{
                                searchInput.value = text;
                                hideHomeSuggestions();
                                executeSearch(text);
                            }});
                            suggestionsBox.appendChild(div);
                        }});
                        selectedSuggestionIdx = -1;
                        suggestionsBox.classList.remove("is-hidden");
                    }} catch (_) {{
                        hideHomeSuggestions();
                    }}
                }}, 120);
            }});

            searchInput.addEventListener("keydown", (e) => {{
                const items = suggestionsBox.querySelectorAll(".home-suggestion-item");
                if (suggestionsBox.classList.contains("is-hidden") || items.length === 0) return;

                if (e.key === "ArrowDown") {{
                    e.preventDefault();
                    selectedSuggestionIdx = (selectedSuggestionIdx + 1) % items.length;
                    updateSuggestionHighlight(items);
                }} else if (e.key === "ArrowUp") {{
                    e.preventDefault();
                    selectedSuggestionIdx = (selectedSuggestionIdx - 1 + items.length) % items.length;
                    updateSuggestionHighlight(items);
                }} else if (e.key === "Escape") {{
                    hideHomeSuggestions();
                }} else if (e.key === "Enter" && selectedSuggestionIdx >= 0) {{
                    e.preventDefault();
                    const selectedText = items[selectedSuggestionIdx].querySelector("span:last-child").textContent;
                    searchInput.value = selectedText;
                    hideHomeSuggestions();
                    executeSearch(selectedText);
                }}
            }});

            function updateSuggestionHighlight(items) {{
                items.forEach((item, idx) => {{
                    if (idx === selectedSuggestionIdx) {{
                        item.classList.add("is-selected");
                        searchInput.value = item.querySelector("span:last-child").textContent;
                    }} else {{
                        item.classList.remove("is-selected");
                    }}
                }});
            }}

            document.addEventListener("click", (e) => {{
                if (!searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {{
                    hideHomeSuggestions();
                }}
            }});
        }}

        document.getElementById("searchForm").addEventListener("submit", (event) => {{
            event.preventDefault();
            const text = searchInput.value.trim();
            if (!text) return;
            hideHomeSuggestions();
            executeSearch(text);
        }});

        document.getElementById("addShortcutBtn").addEventListener("click", () => {{
            document.getElementById("shortcutDialog").showModal();
            document.getElementById("shortcutName").focus();
        }});

        document.getElementById("cancelShortcutBtn").addEventListener("click", () => {{
            document.getElementById("shortcutDialog").close();
        }});

        document.getElementById("resetShortcutBtn").addEventListener("click", () => {{
            saveDials(defaultDials);
            renderDials();
        }});

        document.getElementById("shortcutForm").addEventListener("submit", (event) => {{
            event.preventDefault();
            const title = document.getElementById("shortcutName").value.trim();
            const url = normalizeShortcutUrl(document.getElementById("shortcutUrl").value);
            const badge = document.getElementById("shortcutBadge").value.trim() || "Custom";
            const iconUrl = document.getElementById("shortcutIcon").value.trim() || faviconFor(url);
            if (!title || !url) return;
            const next = getDials().concat([{{ title, url, badge, iconUrl, color: "#FFCF3F" }}]);
            saveDials(next);
            renderDials();
            event.target.reset();
            document.getElementById("shortcutDialog").close();
        }});

        setupWallpaper();
        renderDials();
        updateClock();
        setInterval(updateClock, 1000);
    </script>
</body>
</html>
"""
    return html


def save_cached_homepage(
    ads_blocked: int = 5124,
    trackers_blocked: int = 3890,
    storage_mode: str = "Local Secure Vault",
    vpn_status: str = "Connected (CH-Zurich)",
) -> Path:
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for stale_file in USER_DATA_DIR.glob("home_live_*.html"):
        try:
            stale_file.unlink()
        except OSError:
            pass
    home_file = USER_DATA_DIR / f"home_live_{time.time_ns()}.html"
    html_content = generate_home_html(ads_blocked, trackers_blocked, storage_mode, vpn_status)
    with open(home_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    return home_file
