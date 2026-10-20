"""Lock Down Dedicated Downloads Page Generator.
Serves lockdown://downloads with a high-contrast Yellow & White interface.
Provides real-time download tracking, pause/resume/cancel controls,
file launching, search filtering, and history management.
"""

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


def generate_downloads_html(asset_base_url: str = "") -> str:
    logo_uri = get_logo_data_uri()

    template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Downloads - Lock Down Browser</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        body {
            background: __COLOR_BG__;
            color: __COLOR_TEXT__;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        /* Header */
        header {
            background: __COLOR_HEADER_BG__;
            border-bottom: 2px solid __COLOR_ACCENT__;
            padding: 16px 48px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
            gap: 24px;
        }
        .brand-cluster {
            display: flex;
            align-items: center;
            gap: 16px;
            cursor: pointer;
            text-decoration: none;
            user-select: none;
        }
        .brand-logo {
            width: 40px;
            height: 40px;
            object-fit: contain;
        }
        .brand-title {
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: __COLOR_TEXT__;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .brand-badge {
            font-size: 11px;
            font-weight: 800;
            background: __COLOR_CORAL__;
            color: #FFFFFF;
            padding: 2px 8px;
            border-radius: 10px;
            text-transform: uppercase;
        }
        .brand-subtitle {
            font-size: 13px;
            color: __COLOR_MUTED__;
            font-weight: 500;
        }

        /* Search Bar */
        .search-container {
            flex: 1;
            max-width: 440px;
            position: relative;
        }
        .search-input {
            width: 100%;
            background: #FFFFFF;
            border: 1.5px solid __COLOR_ACCENT__;
            border-radius: 22px;
            padding: 10px 18px 10px 38px;
            font-size: 13.5px;
            color: __COLOR_TEXT__;
            outline: none;
            transition: all 0.2s;
        }
        .search-input:focus {
            border-color: __COLOR_CORAL__;
            box-shadow: 0 0 0 3px rgba(230, 115, 0, 0.15);
        }
        .search-icon {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 14px;
            color: __COLOR_MUTED__;
            pointer-events: none;
        }
        .search-clear {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            font-size: 14px;
            color: __COLOR_MUTED__;
            cursor: pointer;
            display: none;
        }

        /* Header Actions */
        .header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .btn-action {
            background: #FFFFFF;
            border: 1.5px solid __COLOR_ACCENT__;
            color: __COLOR_TEXT__;
            font-weight: 700;
            font-size: 13px;
            padding: 9px 16px;
            border-radius: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 7px;
            transition: all 0.2s;
            text-decoration: none;
            white-space: nowrap;
        }
        .btn-action:hover {
            background: __COLOR_YELLOW_BRIGHT__;
            border-color: __COLOR_CORAL__;
            transform: translateY(-1px);
        }
        .btn-primary {
            background: __COLOR_CORAL__;
            color: #FFFFFF;
            border: 1.5px solid __COLOR_CORAL__;
        }
        .btn-primary:hover {
            background: __COLOR_CORAL_HOVER__;
            border-color: __COLOR_CORAL_HOVER__;
        }

        /* Main Container */
        .container {
            max-width: 1080px;
            margin: 28px auto;
            padding: 0 32px;
            width: 100%;
            flex: 1;
        }

        /* Filter Chips */
        .filter-strip {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 24px;
            overflow-x: auto;
            padding-bottom: 4px;
        }
        .filter-chip {
            background: #FFFFFF;
            border: 1.5px solid __COLOR_ACCENT__;
            padding: 7px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            color: __COLOR_DARK__;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
            user-select: none;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .filter-chip:hover {
            background: __COLOR_HEADER_BG__;
            border-color: __COLOR_CORAL__;
        }
        .filter-chip.active {
            background: __COLOR_CORAL__;
            border-color: __COLOR_CORAL__;
            color: #FFFFFF;
        }

        /* Summary Bar */
        .summary-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            padding: 0 4px;
            font-size: 13.5px;
            color: __COLOR_MUTED__;
            font-weight: 600;
        }
        .summary-count {
            color: __COLOR_TEXT__;
            font-weight: 800;
        }

        /* Downloads List */
        .downloads-list {
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        /* Download Card */
        .download-card {
            background: #FFFFFF;
            border: 1.5px solid __COLOR_ACCENT__;
            border-radius: 14px;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 18px;
            transition: all 0.2s;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
            position: relative;
            overflow: hidden;
        }
        .download-card:hover {
            border-color: __COLOR_CORAL__;
            box-shadow: 0 4px 16px rgba(230, 115, 0, 0.08);
            transform: translateY(-1px);
        }
        .download-card.in-progress {
            border-color: __COLOR_CORAL__;
            background: #FFFEFA;
        }

        /* File Icon */
        .file-icon-box {
            width: 52px;
            height: 52px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
            flex-shrink: 0;
            background: __COLOR_HEADER_BG__;
            border: 1px solid __COLOR_ACCENT__;
        }

        /* File Details */
        .file-details {
            flex: 1;
            min-width: 0;
        }
        .file-title-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 4px;
            flex-wrap: wrap;
        }
        .file-name {
            font-size: 15px;
            font-weight: 800;
            color: __COLOR_TEXT__;
            word-break: break-all;
            cursor: pointer;
            text-decoration: none;
        }
        .file-name:hover {
            color: __COLOR_CORAL__;
            text-decoration: underline;
        }
        .file-name.missing {
            color: #8C8C8C;
            text-decoration: line-through;
            cursor: default;
        }

        /* Status Badge */
        .status-badge {
            font-size: 11px;
            font-weight: 800;
            padding: 2px 8px;
            border-radius: 10px;
            text-transform: uppercase;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .status-badge.in_progress {
            background: rgba(230, 115, 0, 0.15);
            color: __COLOR_CORAL__;
            border: 1px solid __COLOR_CORAL__;
            animation: pulse-glow 1.5s infinite;
        }
        .status-badge.paused {
            background: rgba(24, 144, 255, 0.12);
            color: #1890FF;
            border: 1px solid #1890FF;
        }
        .status-badge.completed {
            background: rgba(82, 196, 26, 0.12);
            color: #389E0D;
            border: 1px solid #52C41A;
        }
        .status-badge.cancelled {
            background: #F5F5F5;
            color: #8C8C8C;
            border: 1px solid #D9D9D9;
        }
        .status-badge.interrupted {
            background: rgba(245, 34, 45, 0.12);
            color: #CF1322;
            border: 1px solid #FF4D4F;
        }

        @keyframes pulse-glow {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.65; }
        }

        /* Meta Row */
        .file-meta {
            font-size: 12.5px;
            color: __COLOR_MUTED__;
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 4px;
        }
        .file-url {
            color: __COLOR_MUTED__;
            text-decoration: none;
            max-width: 320px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .file-url:hover {
            color: __COLOR_CORAL__;
            text-decoration: underline;
        }

        /* Progress Bar */
        .progress-wrapper {
            margin-top: 8px;
            width: 100%;
        }
        .progress-bar-bg {
            height: 6px;
            background: #F0F0F0;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, __COLOR_ACCENT__, __COLOR_CORAL__);
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        .progress-text {
            font-size: 12px;
            font-weight: 700;
            color: __COLOR_CORAL__;
            margin-top: 4px;
            display: flex;
            justify-content: space-between;
        }

        /* Card Actions */
        .card-actions {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }
        .btn-card {
            background: __COLOR_HEADER_BG__;
            border: 1px solid __COLOR_ACCENT__;
            color: __COLOR_TEXT__;
            font-size: 12px;
            font-weight: 700;
            padding: 7px 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            white-space: nowrap;
        }
        .btn-card:hover {
            background: __COLOR_YELLOW_BRIGHT__;
            border-color: __COLOR_CORAL__;
            color: __COLOR_CORAL__;
        }
        .btn-card.primary {
            background: __COLOR_CORAL__;
            color: #FFFFFF;
            border-color: __COLOR_CORAL__;
        }
        .btn-card.primary:hover {
            background: __COLOR_CORAL_HOVER__;
        }
        .btn-card.danger {
            background: transparent;
            border-color: transparent;
            color: #8C8C8C;
            padding: 7px 8px;
        }
        .btn-card.danger:hover {
            background: rgba(245, 34, 45, 0.1);
            color: #CF1322;
        }

        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 80px 20px;
            background: #FFFFFF;
            border: 1.5px dashed __COLOR_ACCENT__;
            border-radius: 18px;
            margin-top: 20px;
        }
        .empty-icon {
            font-size: 56px;
            margin-bottom: 14px;
        }
        .empty-title {
            font-size: 20px;
            font-weight: 800;
            margin-bottom: 8px;
            color: __COLOR_TEXT__;
        }
        .empty-desc {
            font-size: 14px;
            color: __COLOR_MUTED__;
            max-width: 420px;
            margin: 0 auto 20px;
        }

        /* Toast */
        #toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: __COLOR_TEXT__;
            color: #FFFFFF;
            padding: 12px 22px;
            border-radius: 12px;
            font-size: 13.5px;
            font-weight: 700;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            pointer-events: none;
            z-index: 1000;
        }
        #toast.show {
            opacity: 1;
            transform: translateY(0);
        }
    </style>
</head>
<body>

<header>
    <div class="brand-cluster" onclick="window.location.href='/lockdown-home'">
        <img src="__LOGO_URI__" class="brand-logo" alt="Logo">
        <div>
            <div class="brand-title">
                Downloads
                <span class="brand-badge" id="activeCounterBadge" style="display: none;">0 Active</span>
            </div>
            <div class="brand-subtitle">High-speed download manager with pause, resume, file integrity, and folder launcher</div>
        </div>
    </div>

    <div class="search-container">
        <span class="search-icon">🔍</span>
        <input type="text" id="searchInput" class="search-input" placeholder="Search downloaded files or source URLs..." oninput="onSearchInput()">
        <button id="searchClearBtn" class="search-clear" onclick="clearSearch()">✕</button>
    </div>

    <div class="header-actions">
        <button class="btn-action" onclick="openDownloadsFolder()" title="Open default download folder">
            <span>📁</span> Open Folder
        </button>
        <button class="btn-action" onclick="clearCompletedDownloads()" title="Remove finished downloads from list">
            <span>🧹</span> Clear Completed
        </button>
        <button class="btn-action" onclick="window.location.href='/lockdown-home'">
            <span>🏠</span> Home
        </button>
    </div>
</header>

<div class="container">
    <!-- Filter Strip -->
    <div class="filter-strip">
        <button class="filter-chip active" onclick="setFilter('all', this)"><span>📋</span> All Files</button>
        <button class="filter-chip" onclick="setFilter('active', this)"><span>⏳</span> In Progress</button>
        <button class="filter-chip" onclick="setFilter('completed', this)"><span>✅</span> Completed</button>
        <button class="filter-chip" onclick="setFilter('document', this)"><span>📄</span> Documents</button>
        <button class="filter-chip" onclick="setFilter('image', this)"><span>🖼️</span> Images</button>
        <button class="filter-chip" onclick="setFilter('media', this)"><span>🎬</span> Media</button>
        <button class="filter-chip" onclick="setFilter('archive', this)"><span>📦</span> Archives</button>
        <button class="filter-chip" onclick="setFilter('installer', this)"><span>⚡</span> Installers</button>
    </div>

    <!-- Summary Bar -->
    <div class="summary-bar">
        <div>Showing <span id="visibleCount" class="summary-count">0</span> downloads</div>
        <div id="transferSummary" style="font-size: 12.5px; color: __COLOR_CORAL__; font-weight: 700;"></div>
    </div>

    <!-- Downloads Container -->
    <div id="downloadsList" class="downloads-list">
        <!-- Rendered dynamically -->
    </div>

    <!-- Empty State -->
    <div id="emptyState" class="empty-state" style="display: none;">
        <div class="empty-icon">📥</div>
        <div class="empty-title" id="emptyTitle">No downloads yet</div>
        <div class="empty-desc" id="emptyDesc">Files downloaded from web pages will be tracked and displayed here with live progress and quick actions.</div>
        <button class="btn-action btn-primary" style="margin: 0 auto;" onclick="openDownloadsFolder()">
            <span>📁</span> Open Downloads Folder
        </button>
    </div>
</div>

<div id="toast"></div>

<script>
    let allDownloads = [];
    let currentFilter = 'all';
    let searchQuery = '';

    async function fetchDownloads() {
        try {
            const res = await fetch('/api/downloads/list');
            if (res.ok) {
                const data = await res.json();
                allDownloads = data.downloads || [];
                renderDownloads();
                updateActiveBadge(data.active_count || 0);
            }
        } catch (e) {
            console.error('Failed fetching downloads:', e);
        }
    }

    function renderDownloads() {
        const listEl = document.getElementById('downloadsList');
        const emptyEl = document.getElementById('emptyState');
        const emptyTitle = document.getElementById('emptyTitle');
        const emptyDesc = document.getElementById('emptyDesc');
        const visibleCountEl = document.getElementById('visibleCount');
        const transferSummary = document.getElementById('transferSummary');

        const filtered = allDownloads.filter(item => {
            // Category filter
            if (currentFilter === 'active') {
                if (item.state !== 'in_progress' && item.state !== 'paused') return false;
            } else if (currentFilter === 'completed') {
                if (item.state !== 'completed') return false;
            } else if (currentFilter === 'media') {
                if (item.category !== 'video' && item.category !== 'audio') return false;
            } else if (currentFilter !== 'all') {
                if (item.category !== currentFilter) return false;
            }

            // Search query filter
            if (searchQuery) {
                const q = searchQuery.toLowerCase();
                const fn = (item.filename || '').toLowerCase();
                const u = (item.url || '').toLowerCase();
                if (!fn.includes(q) && !u.includes(q)) return false;
            }

            return true;
        });

        visibleCountEl.innerText = filtered.length;

        // Calculate active transfer speeds
        const activeItems = allDownloads.filter(i => i.state === 'in_progress');
        if (activeItems.length > 0) {
            const totalSpeed = activeItems.reduce((acc, curr) => acc + (curr.speed_bps || 0), 0);
            transferSummary.innerText = `⚡ Downloading ${activeItems.length} file${activeItems.length > 1 ? 's' : ''} • ${formatSpeed(totalSpeed)}`;
        } else {
            transferSummary.innerText = '';
        }

        if (filtered.length === 0) {
            listEl.innerHTML = '';
            emptyEl.style.display = 'block';
            if (searchQuery) {
                emptyTitle.innerText = 'No matching downloads';
                emptyDesc.innerText = `No downloaded files matched '${searchQuery}'.`;
            } else if (currentFilter !== 'all') {
                emptyTitle.innerText = `No ${currentFilter} downloads`;
                emptyDesc.innerText = `You don't have any files in the ${currentFilter} category.`;
            } else {
                emptyTitle.innerText = 'No downloads yet';
                emptyDesc.innerText = 'Files downloaded from websites will appear here with complete speed, progress, and file controls.';
            }
            return;
        }

        emptyEl.style.display = 'none';

        listEl.innerHTML = filtered.map(item => {
            const isProgress = item.state === 'in_progress';
            const isPaused = item.state === 'paused';
            const isCompleted = item.state === 'completed';
            const isCancelled = item.state === 'cancelled';
            const isInterrupted = item.state === 'interrupted';
            const isMissing = !item.file_exists && isCompleted;

            let statusLabel = 'Completed';
            if (isProgress) statusLabel = `Downloading (${item.progress_percent}%)`;
            else if (isPaused) statusLabel = 'Paused';
            else if (isCancelled) statusLabel = 'Cancelled';
            else if (isInterrupted) statusLabel = 'Interrupted';
            else if (isMissing) statusLabel = 'File Deleted';

            const dateStr = item.start_time ? new Date(item.start_time * 1000).toLocaleString() : '';

            let progressHtml = '';
            if (isProgress || isPaused) {
                progressHtml = `
                    <div class="progress-wrapper">
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: ${item.progress_percent}%;"></div>
                        </div>
                        <div class="progress-text">
                            <span>${item.received_str} of ${item.total_str} ${item.speed_str ? '• ' + item.speed_str : ''}</span>
                            <span>${item.eta_str || (item.progress_percent + '%')}</span>
                        </div>
                    </div>
                `;
            }

            let actionButtons = '';
            if (isProgress) {
                actionButtons = `
                    <button class="btn-card" onclick="pauseDownload('${item.id}')" title="Pause download">⏸ Pause</button>
                    <button class="btn-card danger" onclick="cancelDownload('${item.id}')" title="Cancel download">✕ Cancel</button>
                `;
            } else if (isPaused) {
                actionButtons = `
                    <button class="btn-card primary" onclick="resumeDownload('${item.id}')" title="Resume download">▶ Resume</button>
                    <button class="btn-card danger" onclick="cancelDownload('${item.id}')" title="Cancel download">✕ Cancel</button>
                `;
            } else if (isCompleted) {
                if (!isMissing) {
                    actionButtons = `
                        <button class="btn-card primary" onclick="openFile('${item.id}')" title="Open file with system viewer">📂 Open</button>
                        <button class="btn-card" onclick="showInFolder('${item.id}')" title="Show in Windows Explorer">📁 Folder</button>
                        <button class="btn-card" onclick="copyLink('${item.url}')" title="Copy download link">🔗 Link</button>
                        <button class="btn-card danger" onclick="deleteFile('${item.id}')" title="Delete file from disk">🗑️</button>
                    `;
                } else {
                    actionButtons = `
                        <button class="btn-card" onclick="copyLink('${item.url}')" title="Copy download link">🔗 Link</button>
                        <button class="btn-card danger" onclick="removeDownload('${item.id}')" title="Remove from list">✕ Remove</button>
                    `;
                }
            } else {
                // Cancelled or interrupted
                actionButtons = `
                    <button class="btn-card primary" onclick="retryDownload('${item.url}')" title="Restart download">🔄 Retry</button>
                    <button class="btn-card" onclick="copyLink('${item.url}')" title="Copy download link">🔗 Link</button>
                    <button class="btn-card danger" onclick="removeDownload('${item.id}')" title="Remove from list">✕ Remove</button>
                `;
            }

            return `
                <div class="download-card ${isProgress ? 'in-progress' : ''}" id="card-${item.id}">
                    <div class="file-icon-box" style="border-color: ${item.color}30; background: ${item.color}10;">
                        ${item.icon}
                    </div>

                    <div class="file-details">
                        <div class="file-title-row">
                            <span class="file-name ${isMissing ? 'missing' : ''}" onclick="${isCompleted && !isMissing ? `openFile('${item.id}')` : ''}" title="${escapeHtml(item.filepath || item.filename)}">
                                ${escapeHtml(item.filename)}
                            </span>
                            <span class="status-badge ${item.state}">${statusLabel}</span>
                        </div>

                        ${progressHtml}

                        <div class="file-meta">
                            <span>${item.total_str || item.received_str}</span>
                            <span>•</span>
                            <span>${dateStr}</span>
                            ${item.url ? `<span>•</span><a href="${escapeHtml(item.url)}" target="_blank" class="file-url" title="${escapeHtml(item.url)}">${escapeHtml(cleanUrl(item.url))}</a>` : ''}
                        </div>
                    </div>

                    <div class="card-actions">
                        ${actionButtons}
                    </div>
                </div>
            `;
        }).join('');
    }

    function updateActiveBadge(count) {
        const badge = document.getElementById('activeCounterBadge');
        if (count > 0) {
            badge.innerText = `${count} Active`;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }

    // ── Actions ──
    async function pauseDownload(id) {
        await postApi('/api/downloads/pause', { id });
        fetchDownloads();
        showToast('⏸ Download paused');
    }

    async function resumeDownload(id) {
        await postApi('/api/downloads/resume', { id });
        fetchDownloads();
        showToast('▶ Resuming download...');
    }

    async function cancelDownload(id) {
        await postApi('/api/downloads/cancel', { id });
        fetchDownloads();
        showToast('✕ Download cancelled');
    }

    async function openFile(id) {
        const res = await postApi('/api/downloads/open', { id });
        if (res && !res.success) {
            showToast('⚠️ Could not open file (it may have been moved or deleted)');
            fetchDownloads();
        }
    }

    async function showInFolder(id) {
        await postApi('/api/downloads/show_in_folder', { id });
    }

    async function openDownloadsFolder() {
        await postApi('/api/downloads/open_folder', {});
    }

    async function removeDownload(id) {
        await postApi('/api/downloads/remove', { id });
        fetchDownloads();
        showToast('Removed from downloads list');
    }

    async function deleteFile(id) {
        if (confirm('Are you sure you want to delete this file from your disk?')) {
            await postApi('/api/downloads/delete_file', { id });
            fetchDownloads();
            showToast('🗑️ File deleted from disk');
        }
    }

    async function clearCompletedDownloads() {
        const res = await postApi('/api/downloads/clear_completed', {});
        fetchDownloads();
        showToast(`🧹 Cleared ${res.count || 0} completed downloads`);
    }

    function retryDownload(url) {
        if (url) {
            window.location.href = url;
            showToast('🔄 Restarting download...');
        }
    }

    function copyLink(url) {
        if (navigator.clipboard && url) {
            navigator.clipboard.writeText(url);
            showToast('✓ Download link copied to clipboard');
        }
    }

    // ── Search & Filter ──
    function setFilter(cat, btn) {
        currentFilter = cat;
        document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
        if (btn) btn.classList.add('active');
        renderDownloads();
    }

    function onSearchInput() {
        const inp = document.getElementById('searchInput');
        const clearBtn = document.getElementById('searchClearBtn');
        searchQuery = inp.value.trim();
        clearBtn.style.display = searchQuery ? 'block' : 'none';
        renderDownloads();
    }

    function clearSearch() {
        const inp = document.getElementById('searchInput');
        inp.value = '';
        searchQuery = '';
        document.getElementById('searchClearBtn').style.display = 'none';
        renderDownloads();
        inp.focus();
    }

    // ── Utilities ──
    async function postApi(url, data) {
        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await res.json();
        } catch (e) {
            console.error('API error:', e);
            return { success: false };
        }
    }

    function formatSpeed(bps) {
        if (!bps || bps <= 0) return '0 KB/s';
        if (bps < 1024) return Math.round(bps) + ' B/s';
        if (bps < 1024 * 1024) return (bps / 1024).toFixed(1) + ' KB/s';
        return (bps / (1024 * 1024)).toFixed(1) + ' MB/s';
    }

    function cleanUrl(u) {
        try {
            const url = new URL(u);
            return url.hostname + url.pathname.slice(0, 24) + (url.pathname.length > 24 ? '...' : '');
        } catch (_) {
            return u.slice(0, 32);
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function showToast(msg) {
        const t = document.getElementById('toast');
        t.innerText = msg;
        t.classList.add('show');
        setTimeout(() => { t.classList.remove('show'); }, 3000);
    }

    // ── Lifecycle ──
    fetchDownloads();
    // Poll every 1.2s
    setInterval(() => {
        fetchDownloads();
    }, 1200);
</script>

</body>
</html>
"""

    return (
        template
        .replace("__COLOR_BG__", COLOR_BLUE_DARKEST)
        .replace("__COLOR_HEADER_BG__", COLOR_YELLOW_SOFT)
        .replace("__COLOR_ACCENT__", COLOR_YELLOW_ACCENT)
        .replace("__COLOR_YELLOW_BRIGHT__", COLOR_YELLOW_BRIGHT)
        .replace("__COLOR_CORAL__", COLOR_CORAL_PRIMARY)
        .replace("__COLOR_CORAL_HOVER__", COLOR_CORAL_HOVER)
        .replace("__COLOR_TEXT__", COLOR_IVORY_LIGHT)
        .replace("__COLOR_MUTED__", COLOR_IVORY_MUTED)
        .replace("__COLOR_DARK__", COLOR_IVORY_DARK)
        .replace("__LOGO_URI__", logo_uri)
    )
