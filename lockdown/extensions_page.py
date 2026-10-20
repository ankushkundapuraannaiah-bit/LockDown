"""Lock Down Extensions Hub & Manager Page Generator.
Serves lockdown://extensions with a Yellow & White high-contrast interface.
Supports live toggling, online downloading from libraries/URLs, 1-click install, and custom folder importing.
"""

from typing import Any, Dict, List
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
)
from lockdown.homepage import get_logo_data_uri


def generate_extensions_html(installed: List[Dict[str, Any]], library: List[Dict[str, Any]], asset_base_url: str = "") -> str:
    logo_uri = get_logo_data_uri()
    installed_count = len(installed)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Extensions - Lock Down Browser</title>
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
            padding-bottom: 60px;
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
            width: 42px;
            height: 42px;
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
        .header-actions {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .search-input {{
            padding: 9px 16px;
            border-radius: 20px;
            border: 1.5px solid {COLOR_YELLOW_ACCENT};
            background: #FFFFFF;
            color: {COLOR_IVORY_LIGHT};
            font-size: 13.5px;
            outline: none;
            width: 230px;
            transition: all 0.2s;
        }}
        .search-input:focus {{
            border-color: {COLOR_CORAL_PRIMARY};
            width: 270px;
            box-shadow: 0 0 0 3px rgba(230, 115, 0, 0.15);
        }}
        .btn-action {{
            background: #FFFFFF;
            border: 1.5px solid {COLOR_YELLOW_ACCENT};
            color: {COLOR_IVORY_LIGHT};
            font-weight: 700;
            font-size: 13px;
            padding: 9px 16px;
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

        /* Navigation Tabs */
        .tab-bar {{
            max-width: 1200px;
            margin: 28px auto 0;
            padding: 0 32px;
            display: flex;
            gap: 8px;
            border-bottom: 2px solid rgba(240, 192, 0, 0.3);
        }}
        .tab-btn {{
            padding: 12px 24px;
            font-size: 15px;
            font-weight: 700;
            background: transparent;
            border: none;
            color: {COLOR_IVORY_MUTED};
            cursor: pointer;
            position: relative;
            display: flex;
            align-items: center;
            gap: 8px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            transition: all 0.2s;
        }}
        .tab-btn:hover {{
            color: {COLOR_IVORY_LIGHT};
            background: rgba(255, 245, 184, 0.4);
        }}
        .tab-btn.active {{
            color: {COLOR_CORAL_PRIMARY};
            background: #FFFFFF;
            border: 2px solid rgba(240, 192, 0, 0.3);
            border-bottom: 2px solid #FFFFFF;
            margin-bottom: -2px;
        }}
        .tab-badge {{
            background: {COLOR_YELLOW_BRIGHT};
            color: {COLOR_IVORY_LIGHT};
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 800;
        }}
        .tab-btn.active .tab-badge {{
            background: {COLOR_CORAL_PRIMARY};
            color: #FFFFFF;
        }}

        /* Main Content Container */
        .container {{
            max-width: 1200px;
            margin: 24px auto 0;
            padding: 0 32px;
        }}

        /* Online Download Hero Bar */
        .online-download-bar {{
            background: #FFFFFF;
            border: 2px solid {COLOR_YELLOW_ACCENT};
            border-radius: 16px;
            padding: 18px 24px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            box-shadow: 0 4px 16px rgba(240, 192, 0, 0.15);
        }}
        .online-bar-icon {{
            font-size: 28px;
            background: {COLOR_YELLOW_SOFT};
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .online-bar-info {{
            flex: 1;
        }}
        .online-bar-title {{
            font-size: 15px;
            font-weight: 800;
            color: {COLOR_IVORY_LIGHT};
            margin-bottom: 3px;
        }}
        .online-bar-desc {{
            font-size: 12px;
            color: {COLOR_IVORY_MUTED};
        }}
        .online-input-row {{
            display: flex;
            gap: 10px;
            margin-top: 8px;
        }}
        .online-input {{
            flex: 1;
            padding: 8px 14px;
            border-radius: 10px;
            border: 1.5px solid {COLOR_YELLOW_ACCENT};
            font-size: 13px;
            outline: none;
            background: {COLOR_BLUE_DARKEST};
            color: {COLOR_IVORY_LIGHT};
        }}
        .online-input:focus {{
            border-color: {COLOR_CORAL_PRIMARY};
            background: #FFFFFF;
        }}

        /* Filter Chips */
        .chips-row {{
            margin-top: 10px;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .chip-btn {{
            padding: 6px 14px;
            border-radius: 16px;
            font-size: 12.5px;
            font-weight: 700;
            cursor: pointer;
            border: 1px solid {COLOR_YELLOW_ACCENT};
            background: {COLOR_YELLOW_SOFT};
            color: {COLOR_IVORY_LIGHT};
            transition: all 0.2s;
        }}
        .chip-btn:hover, .chip-btn.active {{
            background: {COLOR_CORAL_PRIMARY};
            color: #FFFFFF;
            border-color: {COLOR_CORAL_PRIMARY};
        }}

        /* Cards Grid */
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .ext-card {{
            background: #FFFFFF;
            border: 1.5px solid {COLOR_YELLOW_ACCENT};
            border-radius: 16px;
            padding: 22px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
            position: relative;
        }}
        .ext-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(240, 192, 0, 0.25);
            border-color: {COLOR_CORAL_PRIMARY};
        }}
        .card-top {{
            display: flex;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 14px;
        }}
        .card-icon {{
            font-size: 32px;
            background: {COLOR_YELLOW_SOFT};
            width: 54px;
            height: 54px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
            border: 1px solid {COLOR_YELLOW_ACCENT};
            flex-shrink: 0;
        }}
        .card-header {{
            flex: 1;
        }}
        .card-title {{
            font-size: 16.5px;
            font-weight: 800;
            color: {COLOR_IVORY_LIGHT};
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .card-ver {{
            font-size: 11px;
            background: {COLOR_BLUE_SURFACE};
            color: {COLOR_IVORY_DARK};
            padding: 2px 6px;
            border-radius: 6px;
            font-weight: 600;
        }}
        .card-category {{
            font-size: 11px;
            color: {COLOR_CORAL_PRIMARY};
            font-weight: 700;
            margin-top: 2px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .online-badge {{
            font-size: 10px;
            background: rgba(39, 174, 96, 0.15);
            color: #1E8449;
            border: 1px solid #27AE60;
            padding: 2px 7px;
            border-radius: 8px;
            font-weight: 800;
        }}
        .builtin-badge {{
            font-size: 10px;
            background: rgba(230, 115, 0, 0.12);
            color: {COLOR_CORAL_PRIMARY};
            border: 1px solid {COLOR_YELLOW_ACCENT};
            padding: 2px 7px;
            border-radius: 8px;
            font-weight: 800;
        }}
        .card-desc {{
            font-size: 13.5px;
            color: {COLOR_IVORY_DARK};
            line-height: 1.5;
            margin-bottom: 18px;
            flex: 1;
        }}
        .card-footer {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-top: 14px;
            border-top: 1px solid rgba(240, 192, 0, 0.2);
        }}
        .author-tag {{
            font-size: 11.5px;
            color: {COLOR_IVORY_MUTED};
        }}

        /* Switch Toggle */
        .switch-label {{
            position: relative;
            display: inline-block;
            width: 44px;
            height: 24px;
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

        .btn-card-action {{
            padding: 8px 16px;
            border-radius: 16px;
            font-size: 12.5px;
            font-weight: 700;
            cursor: pointer;
            border: 1px solid {COLOR_YELLOW_ACCENT};
            background: {COLOR_YELLOW_SOFT};
            color: {COLOR_IVORY_LIGHT};
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .btn-card-action:hover {{
            background: {COLOR_YELLOW_BRIGHT};
            border-color: {COLOR_CORAL_PRIMARY};
        }}
        .btn-online-dl {{
            background: {COLOR_CORAL_PRIMARY};
            color: #FFFFFF;
            border: 1px solid {COLOR_CORAL_PRIMARY};
        }}
        .btn-online-dl:hover {{
            background: {COLOR_CORAL_HOVER};
            border-color: {COLOR_CORAL_HOVER};
        }}
        .btn-uninstall {{
            background: transparent;
            border: none;
            color: #C0392B;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            padding: 6px 10px;
            border-radius: 8px;
        }}
        .btn-uninstall:hover {{
            background: rgba(192, 57, 43, 0.1);
        }}

        /* Empty State */
        .empty-box {{
            text-align: center;
            padding: 60px 20px;
            background: #FFFFFF;
            border: 2px dashed {COLOR_YELLOW_ACCENT};
            border-radius: 16px;
            margin-top: 24px;
        }}
        .empty-icon {{
            font-size: 48px;
            margin-bottom: 12px;
        }}
        .empty-title {{
            font-size: 20px;
            font-weight: 800;
            margin-bottom: 8px;
        }}
        .empty-subtitle {{
            font-size: 14px;
            color: {COLOR_IVORY_MUTED};
            max-width: 480px;
            margin: 0 auto 20px;
            line-height: 1.5;
        }}

        /* Toast Notifications */
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
            max-width: 420px;
        }}
        #toast.show {{
            opacity: 1;
            transform: translateY(0);
        }}
    </style>
</head>
<body>

<header>
    <div class="brand-cluster">
        <img src="{logo_uri}" class="brand-logo" alt="Logo">
        <div>
            <div class="brand-title">Extensions</div>
            <div class="brand-subtitle">Manage installed extensions or download new ones from our curated library & online cloud</div>
        </div>
    </div>
    <div class="header-actions">
        <input type="text" id="searchInput" class="search-input" placeholder="Search extensions..." oninput="filterCards()">
        <button class="btn-action" onclick="installUnpackedPrompt()">
            <span>➕</span> Load Unpacked
        </button>
        <button class="btn-action btn-primary" onclick="switchTab('library')">
            <span>🛒</span> Browse Library
        </button>
    </div>
</header>

<div class="tab-bar">
    <button id="tabInstalledBtn" class="tab-btn active" onclick="switchTab('installed')">
        <span>🧩</span> My Extensions
        <span id="installedCountBadge" class="tab-badge">{installed_count}</span>
    </button>
    <button id="tabLibraryBtn" class="tab-btn" onclick="switchTab('library')">
        <span>🛒</span> Extension Library & Online Store
        <span class="tab-badge">{len(library)}</span>
    </button>
</div>

<div class="container">
    <!-- View 1: Installed Extensions -->
    <div id="installedSection">
        <div id="installedGrid" class="grid"></div>
        <div id="installedEmpty" class="empty-box" style="display: none;">
            <div class="empty-icon">🧩</div>
            <div class="empty-title">No Extensions Installed Yet</div>
            <div class="empty-subtitle">Enhance your web experience by downloading extensions from our online store or selecting from the built-in library.</div>
            <button class="btn-action btn-primary" style="margin: 0 auto;" onclick="switchTab('library')">
                Explore Extension Library & Online Store
            </button>
        </div>
    </div>

    <!-- View 2: Extension Library & Online Store -->
    <div id="librarySection" style="display: none;">
        <!-- Online Download Bar -->
        <div class="online-download-bar">
            <div class="online-bar-icon">🌐</div>
            <div class="online-bar-info">
                <div class="online-bar-title">Download Extension from Online URL</div>
                <div class="online-bar-desc">Enter any direct online link to a WebExtension (.zip, .crx, or GitHub release) to download and install automatically:</div>
                <div class="online-input-row">
                    <input type="text" id="onlineUrlInput" class="online-input" placeholder="https://github.com/.../release.zip or online .crx / .zip link">
                    <button id="onlineDlBtn" class="btn-action btn-primary" onclick="downloadFromUrl()">
                        <span>📥</span> Download from Online
                    </button>
                </div>
            </div>
        </div>

        <div class="chips-row">
            <button class="chip-btn active" onclick="filterCategory('all', this)">All Extensions</button>
            <button class="chip-btn" onclick="filterCategory('online', this)">🌐 Online Downloads</button>
            <button class="chip-btn" onclick="filterCategory('builtin', this)">📦 Built-in</button>
            <button class="chip-btn" onclick="filterCategory('Privacy & Security', this)">🛡️ Privacy & Security</button>
            <button class="chip-btn" onclick="filterCategory('Productivity', this)">⚡ Productivity</button>
            <button class="chip-btn" onclick="filterCategory('Developer Tools', this)">🛠️ Developer Tools</button>
            <button class="chip-btn" onclick="filterCategory('Appearance', this)">🎨 Appearance</button>
        </div>

        <div id="libraryGrid" class="grid"></div>
    </div>
</div>

<div id="toast"></div>

<script>
    let installedData = [];
    let libraryData = [];
    let activeFilter = 'all';

    async function loadData() {{
        try {{
            const res = await fetch('/api/extensions/list');
            const data = await res.json();
            installedData = data.installed || [];
            libraryData = data.library || [];
            renderInstalled();
            renderLibrary();
        }} catch(e) {{
            console.error('Error loading extensions:', e);
        }}
    }}

    function switchTab(tab) {{
        const instSec = document.getElementById('installedSection');
        const libSec = document.getElementById('librarySection');
        const instBtn = document.getElementById('tabInstalledBtn');
        const libBtn = document.getElementById('tabLibraryBtn');

        if (tab === 'installed') {{
            instSec.style.display = 'block';
            libSec.style.display = 'none';
            instBtn.classList.add('active');
            libBtn.classList.remove('active');
        }} else {{
            instSec.style.display = 'block';
            libSec.style.display = 'block';
            instBtn.classList.remove('active');
            libBtn.classList.add('active');
            instSec.style.display = 'none';
        }}
        filterCards();
    }}

    function renderInstalled() {{
        const grid = document.getElementById('installedGrid');
        const empty = document.getElementById('installedEmpty');
        const badge = document.getElementById('installedCountBadge');
        badge.innerText = installedData.length;

        if (installedData.length === 0) {{
            grid.innerHTML = '';
            empty.style.display = 'block';
            return;
        }}
        empty.style.display = 'none';

        grid.innerHTML = installedData.map(ext => `
            <div class="ext-card" data-name="${{ext.name.toLowerCase()}}" data-desc="${{ext.description.toLowerCase()}}">
                <div>
                    <div class="card-top">
                        <div class="card-icon">${{ext.icon || '🧩'}}</div>
                        <div class="card-header">
                            <div class="card-title">
                                ${{ext.name}}
                                <span class="card-ver">v${{ext.version}}</span>
                            </div>
                            <div class="card-category">${{ext.category || 'Extension'}}</div>
                        </div>
                    </div>
                    <div class="card-desc">${{ext.description}}</div>
                </div>
                <div class="card-footer">
                    <div>
                        <button class="btn-uninstall" onclick="uninstallExtension('${{ext.id}}')">🗑️ Remove</button>
                    </div>
                    <label class="switch-label">
                        <input type="checkbox" ${{ext.enabled ? 'checked' : ''}} onchange="toggleExtension('${{ext.id}}', this.checked)">
                        <span class="slider"></span>
                    </label>
                </div>
            </div>
        `).join('');
    }}

    function renderLibrary() {{
        const grid = document.getElementById('libraryGrid');
        const installedIds = new Set(installedData.map(e => e.id));

        grid.innerHTML = libraryData.map(ext => {{
            const isInstalled = installedIds.has(ext.id);
            const isOnline = Boolean(ext.is_online);
            const badgeClass = isOnline ? 'online-badge' : 'builtin-badge';
            const badgeText = isOnline ? '🌐 Online Download' : '📦 Built-in';

            let actionBtn = '';
            if (isInstalled) {{
                actionBtn = '<button class="btn-card-action" style="opacity: 0.6; cursor: default;">✓ Installed</button>';
            }} else if (isOnline) {{
                actionBtn = `<button class="btn-card-action btn-online-dl" onclick="downloadOnlineExtension('${{ext.id}}', '${{ext.download_url || ''}}', this)"><span>📥</span> Download Online</button>`;
            }} else {{
                actionBtn = `<button class="btn-card-action btn-primary" onclick="installLibraryExtension('${{ext.id}}', this)"><span>➕</span> Add to Browser</button>`;
            }}

            return `
                <div class="ext-card" data-category="${{ext.category}}" data-type="${{isOnline ? 'online' : 'builtin'}}" data-name="${{ext.name.toLowerCase()}}" data-desc="${{ext.description.toLowerCase()}}">
                    <div>
                        <div class="card-top">
                            <div class="card-icon">${{ext.icon}}</div>
                            <div class="card-header">
                                <div class="card-title">
                                    ${{ext.name}}
                                    <span class="card-ver">v${{ext.version}}</span>
                                    <span class="${{badgeClass}}">${{badgeText}}</span>
                                </div>
                                <div class="card-category">${{ext.category}}</div>
                            </div>
                        </div>
                        <div class="card-desc">${{ext.description}}</div>
                    </div>
                    <div class="card-footer">
                        <span class="author-tag">By ${{ext.author}}</span>
                        ${{actionBtn}}
                    </div>
                </div>
            `;
        }}).join('');
    }}

    async function toggleExtension(extId, enabled) {{
        try {{
            const res = await fetch('/api/extensions/toggle', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{id: extId, enabled: enabled}})
            }});
            const data = await res.json();
            if (data.success) {{
                showToast(enabled ? 'Extension enabled' : 'Extension disabled');
            }}
        }} catch(e) {{
            showToast('Failed to toggle extension');
        }}
    }}

    async function installLibraryExtension(extId, btn) {{
        if (btn) {{
            btn.disabled = true;
            btn.innerHTML = '<span>⏳</span> Installing...';
        }}
        try {{
            const res = await fetch('/api/extensions/install', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{id: extId}})
            }});
            const data = await res.json();
            if (data.success) {{
                showToast('✓ ' + data.name + ' installed successfully!');
                await loadData();
            }} else {{
                showToast('Install error: ' + (data.error || 'Failed'));
                if (btn) {{ btn.disabled = false; btn.innerHTML = 'Add to Browser'; }}
            }}
        }} catch(e) {{
            showToast('Error communicating with browser server');
            if (btn) {{ btn.disabled = false; btn.innerHTML = 'Add to Browser'; }}
        }}
    }}

    async function downloadOnlineExtension(extId, downloadUrl, btn) {{
        if (btn) {{
            btn.disabled = true;
            btn.innerHTML = '<span>⏳</span> Downloading...';
        }}
        showToast('🌐 Downloading extension from online library...');
        try {{
            const res = await fetch('/api/extensions/download_online', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{id: extId, url: downloadUrl}})
            }});
            const data = await res.json();
            if (data.success) {{
                showToast(data.message || ('✓ ' + data.name + ' downloaded & installed!'));
                await loadData();
            }} else {{
                showToast('Online download error: ' + (data.error || 'Failed'));
                if (btn) {{ btn.disabled = false; btn.innerHTML = '<span>📥</span> Download Online'; }}
            }}
        }} catch(e) {{
            showToast('Network error downloading extension');
            if (btn) {{ btn.disabled = false; btn.innerHTML = '<span>📥</span> Download Online'; }}
        }}
    }}

    async function downloadFromUrl() {{
        const input = document.getElementById('onlineUrlInput');
        const url = (input.value || '').trim();
        if (!url) {{
            showToast('Please enter an online extension download URL (.zip or .crx)');
            input.focus();
            return;
        }}

        const btn = document.getElementById('onlineDlBtn');
        btn.disabled = true;
        btn.innerHTML = '<span>⏳</span> Downloading...';
        showToast('🌐 Connecting and downloading package from online URL...');

        try {{
            const res = await fetch('/api/extensions/download_online', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{url: url}})
            }});
            const data = await res.json();
            if (data.success) {{
                showToast(data.message || ('✓ ' + data.name + ' installed from online!'));
                input.value = '';
                await loadData();
            }} else {{
                showToast('Download error: ' + (data.error || 'Failed to download'));
            }}
        }} catch(e) {{
            showToast('Error downloading online extension: ' + e);
        }} finally {{
            btn.disabled = false;
            btn.innerHTML = '<span>📥</span> Download from Online';
        }}
    }}

    async function uninstallExtension(extId) {{
        if (!confirm('Are you sure you want to remove this extension?')) return;
        try {{
            const res = await fetch('/api/extensions/uninstall', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{id: extId}})
            }});
            const data = await res.json();
            if (data.success) {{
                showToast('Extension removed');
                await loadData();
            }}
        }} catch(e) {{
            showToast('Error removing extension');
        }}
    }}

    async function installUnpackedPrompt() {{
        try {{
            const res = await fetch('/api/extensions/browse_folder', {{method: 'POST'}});
            const data = await res.json();
            if (data.success) {{
                showToast('✓ ' + data.name + ' installed!');
                await loadData();
            }} else if (data.error && data.error !== 'Cancelled') {{
                showToast('Failed: ' + data.error);
            }}
        }} catch(e) {{
            showToast('Error opening directory picker');
        }}
    }}

    function filterCategory(cat, btn) {{
        activeFilter = cat;
        document.querySelectorAll('.chip-btn').forEach(b => b.classList.remove('active'));
        if (btn) btn.classList.add('active');

        const cards = document.querySelectorAll('#libraryGrid .ext-card');
        cards.forEach(card => {{
            const cardCat = card.getAttribute('data-category');
            const cardType = card.getAttribute('data-type');
            let match = false;
            if (cat === 'all') match = true;
            else if (cat === 'online') match = (cardType === 'online');
            else if (cat === 'builtin') match = (cardType === 'builtin');
            else match = (cardCat === cat);

            card.style.display = match ? 'flex' : 'none';
        }});
    }}

    function filterCards() {{
        const q = (document.getElementById('searchInput').value || '').toLowerCase().trim();
        const cards = document.querySelectorAll('.ext-card');
        cards.forEach(card => {{
            const name = card.getAttribute('data-name') || '';
            const desc = card.getAttribute('data-desc') || '';
            const match = !q || name.includes(q) || desc.includes(q);
            card.style.display = match ? 'flex' : 'none';
        }});
    }}

    function showToast(msg) {{
        const t = document.getElementById('toast');
        t.innerText = msg;
        t.classList.add('show');
        setTimeout(() => {{ t.classList.remove('show'); }}, 3800);
    }}

    // Initial load
    loadData();
</script>

</body>
</html>
"""
