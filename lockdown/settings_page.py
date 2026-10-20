"""Lock Down Dedicated Settings Page Generator.
Serves lockdown://settings with a high-contrast Yellow & White / Nocturnal interface.
Provides configuration for Search Engines, Gemini AI Vision, Shields & Anti-Bot,
Proton VPN Tunnel, AES-256-GCM Vault, and Extensions.
"""

from typing import Any, Dict
from lockdown.config import (
    COLOR_BLUE_BASE,
    COLOR_BLUE_BORDER,
    COLOR_BLUE_DARK,
    COLOR_BLUE_DARKEST,
    COLOR_BLUE_SURFACE,
    COLOR_CORAL_HOVER,
    COLOR_CORAL_PRIMARY,
    COLOR_IVORY_DARK,
    COLOR_IVORY_LIGHT,
    COLOR_IVORY_MUTED,
    COLOR_YELLOW_ACCENT,
    COLOR_YELLOW_BRIGHT,
    COLOR_YELLOW_SOFT,
    SEARCH_ENGINES,
)
from lockdown.gemini_service import SUPPORTED_MODELS
from lockdown.homepage import get_logo_data_uri
from lockdown.vpn_service import PROTON_SERVERS


def generate_settings_html(settings: Dict[str, Any], asset_base_url: str = "") -> str:
    logo_uri = get_logo_data_uri()
    current_engine = settings.get("search_engine", "Google")
    gemini_key = settings.get("gemini_api_key", "")
    current_model = settings.get("gemini_model", "gemini-2.5-flash")
    vpn_server = settings.get("vpn_server", "switzerland")
    vpn_proto = settings.get("vpn_protocol", "WireGuard")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Settings - Lock Down Browser</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        body {{
            background: {COLOR_BLUE_DARKEST};
            color: {COLOR_IVORY_LIGHT};
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        /* Header */
        header {{
            background: {COLOR_YELLOW_SOFT};
            border-bottom: 2px solid {COLOR_YELLOW_ACCENT};
            padding: 18px 48px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
        }}
        .brand-cluster {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        .brand-logo {{
            width: 40px;
            height: 40px;
            object-fit: contain;
        }}
        .brand-title {{
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: {COLOR_IVORY_LIGHT};
        }}
        .brand-subtitle {{
            font-size: 13px;
            color: {COLOR_IVORY_MUTED};
            font-weight: 500;
        }}
        .btn-action {{
            background: #FFFFFF;
            border: 1.5px solid {COLOR_YELLOW_ACCENT};
            color: {COLOR_IVORY_LIGHT};
            font-weight: 700;
            font-size: 13px;
            padding: 9px 18px;
            border-radius: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
        }}
        .btn-action:hover {{
            background: {COLOR_YELLOW_BRIGHT};
            border-color: {COLOR_CORAL_PRIMARY};
        }}
        .btn-primary {{
            background: {COLOR_CORAL_PRIMARY};
            color: #FFFFFF;
            border: 1.5px solid {COLOR_CORAL_PRIMARY};
        }}
        .btn-primary:hover {{
            background: {COLOR_CORAL_HOVER};
            border-color: {COLOR_CORAL_HOVER};
        }}

        /* Main Layout */
        .layout {{
            max-width: 1200px;
            margin: 28px auto;
            padding: 0 32px;
            display: flex;
            gap: 32px;
            flex: 1;
            width: 100%;
        }}
        /* Sidebar Nav */
        .sidebar {{
            width: 240px;
            flex-shrink: 0;
        }}
        .nav-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 6px;
            position: sticky;
            top: 96px;
        }}
        .nav-item {{
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 700;
            color: {COLOR_IVORY_DARK};
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: all 0.2s;
        }}
        .nav-item:hover {{
            background: {COLOR_YELLOW_SOFT};
            color: {COLOR_CORAL_PRIMARY};
        }}
        .nav-item.active {{
            background: {COLOR_CORAL_PRIMARY};
            color: #FFFFFF;
        }}

        /* Settings Panels */
        .content {{
            flex: 1;
            max-width: 850px;
        }}
        .panel {{
            display: none;
            background: #FFFFFF;
            border: 1.5px solid {COLOR_YELLOW_ACCENT};
            border-radius: 20px;
            padding: 32px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
            margin-bottom: 24px;
        }}
        .panel.active {{
            display: block;
        }}
        .panel-title {{
            font-size: 20px;
            font-weight: 800;
            margin-bottom: 6px;
            color: {COLOR_IVORY_LIGHT};
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .panel-desc {{
            font-size: 13.5px;
            color: {COLOR_IVORY_MUTED};
            margin-bottom: 24px;
            line-height: 1.5;
            border-bottom: 1px solid rgba(240, 192, 0, 0.25);
            padding-bottom: 16px;
        }}

        /* Form Controls */
        .form-group {{
            margin-bottom: 20px;
        }}
        .form-label {{
            display: block;
            font-size: 13.5px;
            font-weight: 700;
            margin-bottom: 8px;
            color: {COLOR_IVORY_LIGHT};
        }}
        .form-sub {{
            font-size: 12px;
            color: {COLOR_IVORY_MUTED};
            margin-top: 4px;
        }}
        .form-input, .form-select {{
            width: 100%;
            padding: 10px 14px;
            border-radius: 10px;
            border: 1.5px solid {COLOR_YELLOW_ACCENT};
            font-size: 13.5px;
            background: {COLOR_BLUE_DARKEST};
            color: {COLOR_IVORY_LIGHT};
            outline: none;
            transition: border-color 0.2s;
        }}
        .form-input:focus, .form-select:focus {{
            border-color: {COLOR_CORAL_PRIMARY};
            background: #FFFFFF;
        }}

        /* Checkbox Switch Row */
        .check-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 0;
            border-bottom: 1px solid rgba(240, 192, 0, 0.15);
        }}
        .check-info {{
            flex: 1;
            padding-right: 20px;
        }}
        .check-title {{
            font-size: 14px;
            font-weight: 700;
            color: {COLOR_IVORY_LIGHT};
        }}
        .check-desc {{
            font-size: 12px;
            color: {COLOR_IVORY_MUTED};
            margin-top: 2px;
        }}
        .switch-label {{
            position: relative;
            display: inline-block;
            width: 44px;
            height: 24px;
            flex-shrink: 0;
        }}
        .switch-label input {{
            opacity: 0;
            width: 0;
            height: 0;
        }}
        .slider {{
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: #E2DAC8;
            transition: .3s;
            border-radius: 24px;
        }}
        .slider:before {{
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .3s;
            border-radius: 50%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        input:checked + .slider {{
            background-color: {COLOR_CORAL_PRIMARY};
        }}
        input:checked + .slider:before {{
            transform: translateX(20px);
        }}

        /* Buttons & Badges */
        .btn-inline {{
            padding: 8px 16px;
            border-radius: 12px;
            font-size: 12.5px;
            font-weight: 700;
            cursor: pointer;
            border: 1px solid {COLOR_YELLOW_ACCENT};
            background: {COLOR_YELLOW_SOFT};
            color: {COLOR_IVORY_LIGHT};
            transition: all 0.2s;
        }}
        .btn-inline:hover {{
            background: {COLOR_YELLOW_BRIGHT};
            border-color: {COLOR_CORAL_PRIMARY};
        }}
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11.5px;
            font-weight: 700;
            margin-top: 8px;
        }}
        .status-badge.connected {{
            background: rgba(39, 174, 96, 0.15);
            color: #1E8449;
            border: 1px solid #27AE60;
        }}
        .status-badge.unlinked {{
            background: {COLOR_YELLOW_SOFT};
            color: {COLOR_IVORY_DARK};
            border: 1px solid {COLOR_YELLOW_ACCENT};
        }}

        /* Toast */
        #toast {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #18150E;
            color: #FFFFFF;
            padding: 14px 24px;
            border-radius: 20px;
            border: 1.5px solid {COLOR_CORAL_PRIMARY};
            font-size: 13.5px;
            font-weight: 700;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s;
            pointer-events: none;
            z-index: 1000;
        }}
        #toast.show {{
            opacity: 1;
            transform: translateY(0);
        }}
    </style>
</head>
<body>

<header>
    <div class="brand-cluster" onclick="window.location.href='/lockdown-home'" style="cursor: pointer;" title="Back to Home">
        <img src="{logo_uri}" class="brand-logo" alt="Logo">
        <div>
            <div class="brand-title">Settings</div>
            <div class="brand-subtitle">Customize privacy shields, search engine, Gemini AI vision, and VPN tunnel</div>
        </div>
    </div>
    <div style="display: flex; gap: 10px; align-items: center;">
        <button class="btn-action" onclick="window.location.href='/lockdown-home'">
            <span>🏠</span> Home
        </button>
        <button class="btn-action" onclick="window.location.href='/lockdown-downloads'">
            <span>📥</span> Downloads
        </button>
        <button class="btn-action" onclick="window.location.href='/lockdown-extensions'">
            <span>🧩</span> Extensions
        </button>
        <button class="btn-action btn-primary" onclick="saveSettings()">
            <span>💾</span> Save Changes
        </button>
    </div>
</header>

<div class="layout">
    <!-- Sidebar -->
    <div class="sidebar">
        <ul class="nav-list">
            <li class="nav-item active" onclick="showPanel('general', this)"><span>⚙️</span> General & Search</li>
            <li class="nav-item" onclick="showPanel('ai', this)"><span>✨</span> Gemini AI Vision</li>
            <li class="nav-item" onclick="showPanel('shields', this)"><span>🛡️</span> Shields & Anti-Bot</li>
            <li class="nav-item" onclick="showPanel('vpn', this)"><span>🌐</span> Proton VPN</li>
            <li class="nav-item" onclick="showPanel('vault', this)"><span>🔒</span> History Vault</li>
            <li class="nav-item" onclick="showPanel('downloads', this)"><span>📥</span> Downloads</li>
            <li class="nav-item" onclick="showPanel('extensions', this)"><span>🧩</span> Extensions Hub</li>
        </ul>
    </div>

    <!-- Content Area -->
    <div class="content">
        <!-- 1. General & Search -->
        <div id="panel-general" class="panel active">
            <div class="panel-title"><span>⚙️</span> Search Engine & Defaults</div>
            <div class="panel-desc">Configure your preferred search engine with clean anti-bot URL formatting.</div>

            <div class="form-group">
                <label class="form-label">Default Search Engine</label>
                <select id="searchEngineSelect" class="form-select">
                    {"".join(f'<option value="{name}" {"selected" if name == current_engine else ""}>{name}</option>' for name in SEARCH_ENGINES.keys())}
                </select>
                <div class="form-sub">Clean standard query format prevents automated bot flags and verification loops.</div>
            </div>

            <div class="form-group">
                <label class="form-label">Startup Home Page URL</label>
                <input type="text" id="homeUrlInput" class="form-input" value="{settings.get('home_url', 'lockdown://home')}">
                <div class="form-sub">Default: lockdown://home (High-focus speed dial with Samurai warrior wallpaper)</div>
            </div>

            <div class="check-row">
                <div class="check-info">
                    <div class="check-title">Vertical Sidebar Tabs (Zen Style)</div>
                    <div class="check-desc">Display tabs vertically in the left navigation sidebar.</div>
                </div>
                <label class="switch-label">
                    <input type="checkbox" id="verticalTabsCheck" {"checked" if settings.get('vertical_tabs', False) else ""}>
                    <span class="slider"></span>
                </label>
            </div>
        </div>

        <!-- 2. Gemini AI Vision -->
        <div id="panel-ai" class="panel">
            <div class="panel-title"><span>✨</span> Gemini AI Vision Assistant</div>
            <div class="panel-desc">Empower Lock Down with real-time browser screen reasoning, problem solving, and code analysis.</div>

            <div class="form-group">
                <label class="form-label">Google Gemini API Key</label>
                <div style="display: flex; gap: 10px;">
                    <input type="password" id="geminiKeyInput" class="form-input" value="{gemini_key}" placeholder="Paste AIzaSy... key from Google AI Studio">
                    <button class="btn-inline" type="button" onclick="toggleKeyVisibility()">👁️ Show</button>
                    <button class="btn-inline btn-primary" type="button" onclick="testGeminiConnection()">⚡ Verify</button>
                </div>
                <div id="geminiStatusBadge" class="status-badge {'connected' if gemini_key else 'unlinked'}">
                    {'🟢 Gemini Key Configured' if gemini_key else '🟡 No API Key Configured'}
                </div>
                <div class="form-sub" style="margin-top: 8px;">
                    Don't have a key? <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color: {COLOR_CORAL_PRIMARY}; font-weight: 700;">Get a free API Key from Google AI Studio ↗</a>
                </div>
            </div>

            <div class="form-group">
                <label class="form-label">Active Vision Model</label>
                <select id="geminiModelSelect" class="form-select">
                    {"".join(f'<option value="{m["id"]}" {"selected" if m["id"] == current_model else ""}>{m["name"]}</option>' for m in SUPPORTED_MODELS)}
                </select>
                <div class="form-sub">Gemini 2.5 Flash is recommended for ultra-low latency multimodal browser analysis.</div>
            </div>

            <div class="check-row">
                <div class="check-info">
                    <div class="check-title">View Browser Viewport by Default</div>
                    <div class="check-desc">Automatically captures a high-resolution screenshot of the active tab for Gemini to inspect.</div>
                </div>
                <label class="switch-label">
                    <input type="checkbox" id="geminiVisionCheck" {"checked" if settings.get('gemini_view_browser', True) else ""}>
                    <span class="slider"></span>
                </label>
            </div>
        </div>

        <!-- 3. Shields & Anti-Bot -->
        <div id="panel-shields" class="panel">
            <div class="panel-title"><span>🛡️</span> Shields & Anti-Bot Protection</div>
            <div class="panel-desc">uBlock Origin Lite request interception combined with stealth client identity to prevent CAPTCHAs.</div>

            <div class="check-row">
                <div class="check-info">
                    <div class="check-title">Shields Ad & Tracker Blocking</div>
                    <div class="check-desc">Blocks ad servers, telemetry beacons, and cryptominers before network transmission.</div>
                </div>
                <label class="switch-label">
                    <input type="checkbox" id="shieldsCheck" {"checked" if settings.get('shields_enabled', True) else ""}>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="check-row">
                <div class="check-info">
                    <div class="check-title">Anti-Bot & Search Engine Integrity Passthrough</div>
                    <div class="check-desc">Preserves search engine verification tokens and prevents automated bot challenges.</div>
                </div>
                <label class="switch-label">
                    <input type="checkbox" id="antiBotCheck" checked disabled>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="check-row">
                <div class="check-info">
                    <div class="check-title">Cookie Consent Wall Suppression</div>
                    <div class="check-desc">Conceals intrusive GDPR / Cookie consent banners across supported news and blog sites.</div>
                </div>
                <label class="switch-label">
                    <input type="checkbox" id="cookieBannerCheck" {"checked" if settings.get('cookie_banner_blocking', True) else ""}>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="check-row">
                <div class="check-info">
                    <div class="check-title">HTTPS Everywhere Upgrade</div>
                    <div class="check-desc">Automatically upgrades insecure HTTP requests to encrypted HTTPS.</div>
                </div>
                <label class="switch-label">
                    <input type="checkbox" id="httpsCheck" {"checked" if settings.get('https_upgrade', True) else ""}>
                    <span class="slider"></span>
                </label>
            </div>
        </div>

        <!-- 4. Proton VPN -->
        <div id="panel-vpn" class="panel">
            <div class="panel-title"><span>🌐</span> Proton-Inspired Secure VPN Tunnel</div>
            <div class="panel-desc">Route browser traffic through encrypted privacy nodes with DNS leak protection.</div>

            <div class="form-group">
                <label class="form-label">Default VPN Location</label>
                <select id="vpnServerSelect" class="form-select">
                    {"".join(f'<option value="{v["id"]}" {"selected" if v["id"] == vpn_server else ""}>{v["flag"]} {v["name"]} ({v["country"]})</option>' for v in PROTON_SERVERS)}
                </select>
            </div>

            <div class="form-group">
                <label class="form-label">Tunnel Protocol</label>
                <select id="vpnProtoSelect" class="form-select">
                    <option value="WireGuard" {"selected" if vpn_proto == "WireGuard" else ""}>WireGuard (Fastest & Modern)</option>
                    <option value="Stealth" {"selected" if vpn_proto == "Stealth" else ""}>Stealth (Anti-Censorship)</option>
                    <option value="OpenVPN" {"selected" if vpn_proto == "OpenVPN" else ""}>OpenVPN (TCP / UDP)</option>
                </select>
            </div>

            <div class="check-row">
                <div class="check-info">
                    <div class="check-title">Kill Switch Leak Protection</div>
                    <div class="check-desc">Blocks all network connections if the VPN tunnel drops unexpectedly.</div>
                </div>
                <label class="switch-label">
                    <input type="checkbox" id="vpnKillCheck" {"checked" if settings.get('vpn_kill_switch', False) else ""}>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="check-row">
                <div class="check-info">
                    <div class="check-title">DNS-over-HTTPS (DoH via Cloudflare 1.1.1.1)</div>
                    <div class="check-desc">Encrypts all domain resolution queries against ISP snooping.</div>
                </div>
                <label class="switch-label">
                    <input type="checkbox" id="dohCheck" {"checked" if settings.get('doh_enabled', True) else ""}>
                    <span class="slider"></span>
                </label>
            </div>
        </div>

        <!-- 5. History Vault -->
        <div id="panel-vault" class="panel">
            <div class="panel-title"><span>🔒</span> AES-256-GCM Encrypted History Vault</div>
            <div class="panel-desc">Zero-knowledge local and Google Drive encrypted browsing history vault.</div>

            <div class="form-group">
                <label class="form-label">Storage Location</label>
                <div style="font-size: 13px; color: {COLOR_IVORY_DARK}; padding: 10px; background: {COLOR_YELLOW_SOFT}; border-radius: 8px;">
                    📁 <b>Local Vault:</b> ~/.lockdown_browser/secure_vault/history.vault<br>
                    🔐 <b>Algorithm:</b> AES-256-GCM (PBKDF2 200,000 rounds)
                </div>
            </div>

            <div class="check-row">
                <div class="check-info">
                    <div class="check-title">Google Drive Encrypted Sync</div>
                    <div class="check-desc">Sync encrypted vault snapshots to your private Google Drive folder.</div>
                </div>
                <label class="switch-label">
                    <input type="checkbox" id="gdriveSyncCheck" {"checked" if settings.get('gdrive_sync_enabled', False) else ""}>
                    <span class="slider"></span>
                </label>
            </div>
        </div>

        <!-- 6. Downloads -->
        <div id="panel-downloads" class="panel">
            <div class="panel-title"><span>📥</span> Downloads Manager & Location</div>
            <div class="panel-desc">Configure default file save directory and view active/completed downloads.</div>

            <div class="form-group">
                <label class="form-label">Default Download Directory</label>
                <input type="text" id="downloadDirInput" class="form-input" value="{settings.get('download_directory', '')}">
                <div class="form-sub">Files downloaded from websites will be saved to this folder automatically.</div>
            </div>

            <div style="display: flex; gap: 12px; margin-top: 18px;">
                <button class="btn-action" onclick="fetch('/api/downloads/open_folder', {{method: 'POST'}})">
                    <span>📁</span> Open Downloads Folder
                </button>
                <button class="btn-action btn-primary" onclick="window.location.href='/lockdown-downloads'">
                    <span>📥</span> Open Full Downloads Page
                </button>
            </div>
        </div>

        <!-- 7. Extensions -->
        <div id="panel-extensions" class="panel">
            <div class="panel-title"><span>🧩</span> Extensions Hub & Store</div>
            <div class="panel-desc">Manage installed extensions or discover privacy & productivity extensions from the cloud store.</div>

            <div style="text-align: center; padding: 40px 20px; background: {COLOR_YELLOW_SOFT}; border-radius: 16px;">
                <div style="font-size: 42px; margin-bottom: 12px;">🧩</div>
                <div style="font-size: 18px; font-weight: 800; margin-bottom: 8px;">Full Extension Management & Cloud Store</div>
                <div style="font-size: 13.5px; color: {COLOR_IVORY_MUTED}; max-width: 480px; margin: 0 auto 20px;">
                    Install Dark Reader, uBlock Shield Plus, SponsorBlock, SingleFile, or download any custom Chrome extension.
                </div>
                <button class="btn-action btn-primary" style="margin: 0 auto;" onclick="openExtensionsPage()">
                    Open Extensions Hub (lockdown://extensions)
                </button>
            </div>
        </div>
    </div>
</div>

<div id="toast"></div>

<script>
    function showPanel(name, tabEl) {{
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        const target = document.getElementById('panel-' + name);
        if (target) target.classList.add('active');
        if (tabEl) tabEl.classList.add('active');
    }}

    function toggleKeyVisibility() {{
        const inp = document.getElementById('geminiKeyInput');
        inp.type = inp.type === 'password' ? 'text' : 'password';
    }}

    async function testGeminiConnection() {{
        const key = document.getElementById('geminiKeyInput').value.trim();
        const badge = document.getElementById('geminiStatusBadge');
        if (!key) {{
            showToast('Please enter a Gemini API Key to verify');
            return;
        }}
        showToast('⏳ Connecting to Google Gemini API...');
        try {{
            const res = await fetch('/api/settings/verify_gemini', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{api_key: key}})
            }});
            const data = await res.json();
            if (data.valid) {{
                badge.className = 'status-badge connected';
                badge.innerText = '🟢 ' + data.message;
                showToast('✅ Gemini Connected: ' + (data.models ? data.models[0] : 'Ready'));
            }} else {{
                badge.className = 'status-badge unlinked';
                badge.innerText = '❌ Verification Failed';
                showToast('Gemini Error: ' + data.message);
            }}
        }} catch(e) {{
            showToast('Network error verifying Gemini');
        }}
    }}

    async function saveSettings() {{
        const payload = {{
            search_engine: document.getElementById('searchEngineSelect').value,
            home_url: document.getElementById('homeUrlInput').value.trim(),
            vertical_tabs: document.getElementById('verticalTabsCheck').checked,
            gemini_api_key: document.getElementById('geminiKeyInput').value.trim(),
            gemini_model: document.getElementById('geminiModelSelect').value,
            gemini_view_browser: document.getElementById('geminiVisionCheck').checked,
            shields_enabled: document.getElementById('shieldsCheck').checked,
            cookie_banner_blocking: document.getElementById('cookieBannerCheck').checked,
            https_upgrade: document.getElementById('httpsCheck').checked,
            vpn_server: document.getElementById('vpnServerSelect').value,
            vpn_protocol: document.getElementById('vpnProtoSelect').value,
            vpn_kill_switch: document.getElementById('vpnKillCheck').checked,
            doh_enabled: document.getElementById('dohCheck').checked,
            gdrive_sync_enabled: document.getElementById('gdriveSyncCheck').checked,
            download_directory: (document.getElementById('downloadDirInput') ? document.getElementById('downloadDirInput').value.trim() : ''),
        }};

        try {{
            const res = await fetch('/api/settings/save', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(payload)
            }});
            const data = await res.json();
            if (data.success) {{
                showToast('✓ Settings saved successfully!');
            }} else {{
                showToast('Error saving: ' + (data.error || 'Failed'));
            }}
        }} catch(e) {{
            showToast('Error saving settings to browser');
        }}
    }}

    function openExtensionsPage() {{
        window.location.href = '/lockdown-extensions';
    }}

    function showToast(msg) {{
        const t = document.getElementById('toast');
        t.innerText = msg;
        t.classList.add('show');
        setTimeout(() => {{ t.classList.remove('show'); }}, 3500);
    }}
</script>

</body>
</html>
"""
