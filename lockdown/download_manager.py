"""Lock Down Browser Download Manager.
Handles file download interception from QWebEngineProfile, tracking,
pause/resume/cancel controls, speed/ETA calculations, and persistent history.
"""

import json
import os
import subprocess
import sys
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

from lockdown.config import (
    DOWNLOADS_DIR,
    DOWNLOADS_FILE,
    load_settings,
)
from lockdown.qt_compat import (
    QDesktopServices,
    QObject,
    QUrl,
    QWebEngineDownloadRequest,
    pyqtSignal,
)


def format_bytes(num_bytes: int) -> str:
    """Format bytes into human-readable string (KB, MB, GB)."""
    if num_bytes is None or num_bytes < 0:
        return "Unknown size"
    if num_bytes == 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}".replace(".0 ", " ")
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def format_speed(bps: float) -> str:
    """Format bytes per second into human-readable transfer rate."""
    if bps <= 0:
        return "0 KB/s"
    if bps < 1024:
        return f"{bps:.0f} B/s"
    elif bps < 1024 * 1024:
        return f"{bps / 1024:.1f} KB/s"
    elif bps < 1024 * 1024 * 1024:
        return f"{bps / (1024 * 1024):.1f} MB/s"
    else:
        return f"{bps / (1024 * 1024 * 1024):.2f} GB/s"


def format_eta(seconds: float) -> str:
    """Format remaining seconds into human-readable time."""
    if seconds <= 0 or seconds > 86400 * 7:
        return "Calculating..."
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s left"
    elif seconds < 3600:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}m {secs}s left"
    else:
        hrs = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hrs}h {mins}m left"


def get_file_category(filename: str) -> Tuple[str, str, str]:
    """Returns (category, icon_emoji, color_hex) based on filename extension."""
    ext = Path(filename).suffix.lower()
    if ext in [".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".xls", ".xlsx", ".csv", ".ppt", ".pptx", ".epub"]:
        return "document", "📄", "#1890FF"
    elif ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff", ".psd"]:
        return "image", "🖼️", "#52C41A"
    elif ext in [".mp4", ".webm", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".m4v"]:
        return "video", "🎬", "#722ED1"
    elif ext in [".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".wma"]:
        return "audio", "🎵", "#EB2F96"
    elif ext in [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".tgz"]:
        return "archive", "📦", "#FA8C16"
    elif ext in [".exe", ".msi", ".bat", ".cmd", ".ps1", ".apk", ".dmg", ".appimage", ".deb", ".rpm"]:
        return "installer", "⚡", "#E67300"
    elif ext in [".py", ".js", ".ts", ".html", ".htm", ".css", ".json", ".xml", ".c", ".cpp", ".rs", ".go", ".java", ".sh"]:
        return "code", "💻", "#13C2C2"
    else:
        return "other", "📁", "#8C8C8C"


def get_unique_filename(directory: Path, filename: str) -> str:
    """Ensures a non-colliding filename in the target directory."""
    target = directory / filename
    if not target.exists():
        return filename

    p = Path(filename)
    stem = p.stem
    suffix = p.suffix
    counter = 1
    while (directory / f"{stem} ({counter}){suffix}").exists():
        counter += 1
    return f"{stem} ({counter}){suffix}"


class DownloadItem:
    """Represents a single browser download."""

    def __init__(
        self,
        item_id: str,
        filename: str,
        filepath: str,
        url: str,
        mime_type: str = "",
        total_bytes: int = -1,
        state: str = "in_progress",
        start_time: float = None,
        end_time: float = None,
        received_bytes: int = 0,
        error_message: str = "",
    ):
        self.id = item_id
        self.filename = filename
        self.filepath = filepath
        self.url = url
        self.mime_type = mime_type
        self.total_bytes = total_bytes
        self.received_bytes = received_bytes
        self.state = state  # in_progress, paused, completed, cancelled, interrupted
        self.start_time = start_time or time.time()
        self.end_time = end_time
        self.error_message = error_message
        self.qt_download: Optional[QWebEngineDownloadRequest] = None

        # Speed estimation history: deque of (time, received_bytes)
        self.samples: Deque[Tuple[float, int]] = deque(maxlen=8)
        self.speed_bps: float = 0.0
        self.eta_seconds: float = 0.0

    def update_speed_and_eta(self) -> None:
        now = time.time()
        self.samples.append((now, self.received_bytes))

        if len(self.samples) >= 2:
            oldest_time, oldest_bytes = self.samples[0]
            dt = now - oldest_time
            db = self.received_bytes - oldest_bytes
            if dt > 0.1 and db >= 0:
                self.speed_bps = db / dt
                if self.total_bytes > 0 and self.speed_bps > 0:
                    remaining_bytes = max(0, self.total_bytes - self.received_bytes)
                    self.eta_seconds = remaining_bytes / self.speed_bps
                else:
                    self.eta_seconds = 0.0
        else:
            self.speed_bps = 0.0
            self.eta_seconds = 0.0

    def to_dict(self) -> Dict[str, Any]:
        cat, icon, color = get_file_category(self.filename)
        pct = 0
        if self.total_bytes > 0:
            pct = min(100, int((self.received_bytes / self.total_bytes) * 100))

        file_exists = os.path.exists(self.filepath)

        return {
            "id": self.id,
            "filename": self.filename,
            "filepath": self.filepath,
            "url": self.url,
            "mime_type": self.mime_type,
            "received_bytes": self.received_bytes,
            "total_bytes": self.total_bytes,
            "received_str": format_bytes(self.received_bytes),
            "total_str": format_bytes(self.total_bytes) if self.total_bytes > 0 else "Unknown size",
            "progress_percent": pct,
            "state": self.state,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "speed_bps": self.speed_bps,
            "speed_str": format_speed(self.speed_bps) if self.state == "in_progress" else "",
            "eta_str": format_eta(self.eta_seconds) if self.state == "in_progress" else "",
            "error_message": self.error_message,
            "category": cat,
            "icon": icon,
            "color": color,
            "file_exists": file_exists,
            "can_pause": self.state == "in_progress",
            "can_resume": self.state == "paused",
            "can_cancel": self.state in ("in_progress", "paused"),
            "can_retry": self.state in ("cancelled", "interrupted"),
            "is_finished": self.state in ("completed", "cancelled", "interrupted"),
        }


class DownloadManager(QObject):
    """Singleton Download Manager coordinating WebEngine downloads and UI."""

    download_started = pyqtSignal(dict)
    download_progress = pyqtSignal(dict)
    download_finished = pyqtSignal(dict)
    downloads_changed = pyqtSignal()

    _instance: Optional["DownloadManager"] = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._downloads: Dict[str, DownloadItem] = {}
        self._load_from_disk()

    @classmethod
    def get_instance(cls) -> "DownloadManager":
        if cls._instance is None:
            cls._instance = DownloadManager()
        return cls._instance

    # -----------------------------------------------------------------------
    # Directory Configuration
    # -----------------------------------------------------------------------
    def get_download_directory(self) -> Path:
        settings = load_settings()
        dir_str = settings.get("download_directory", "").strip()
        if dir_str:
            d = Path(dir_str)
            try:
                d.mkdir(parents=True, exist_ok=True)
                return d
            except Exception:
                pass
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        return DOWNLOADS_DIR

    # -----------------------------------------------------------------------
    # Intercept and Accept Downloads
    # -----------------------------------------------------------------------
    def handle_download_request(self, download: QWebEngineDownloadRequest) -> DownloadItem:
        """Called when QWebEngineProfile.downloadRequested fires."""
        target_dir = self.get_download_directory()
        raw_name = download.suggestedFileName() or download.downloadFileName() or "download"
        clean_name = get_unique_filename(target_dir, raw_name)
        full_path = str(target_dir / clean_name)

        download.setDownloadDirectory(str(target_dir))
        download.setDownloadFileName(clean_name)

        item_id = uuid.uuid4().hex[:12]
        item = DownloadItem(
            item_id=item_id,
            filename=clean_name,
            filepath=full_path,
            url=download.url().toString(),
            mime_type=download.mimeType(),
            total_bytes=download.totalBytes(),
            received_bytes=download.receivedBytes(),
            state="in_progress",
        )
        item.qt_download = download
        self._downloads[item_id] = item

        # Connect QtWebEngine signals
        download.receivedBytesChanged.connect(lambda: self._on_bytes_changed(item_id))
        download.totalBytesChanged.connect(lambda: self._on_total_bytes_changed(item_id))
        download.stateChanged.connect(lambda state: self._on_state_changed(item_id, state))
        download.isPausedChanged.connect(lambda: self._on_paused_changed(item_id))

        # Accept download
        download.accept()

        self._save_to_disk()
        data = item.to_dict()
        self.download_started.emit(data)
        self.downloads_changed.emit()
        return item

    # -----------------------------------------------------------------------
    # Signal Callbacks
    # -----------------------------------------------------------------------
    def _on_bytes_changed(self, item_id: str) -> None:
        item = self._downloads.get(item_id)
        if not item or not item.qt_download:
            return

        item.received_bytes = item.qt_download.receivedBytes()
        item.update_speed_and_eta()
        self.download_progress.emit(item.to_dict())

    def _on_total_bytes_changed(self, item_id: str) -> None:
        item = self._downloads.get(item_id)
        if not item or not item.qt_download:
            return
        item.total_bytes = item.qt_download.totalBytes()
        self.download_progress.emit(item.to_dict())

    def _on_paused_changed(self, item_id: str) -> None:
        item = self._downloads.get(item_id)
        if not item or not item.qt_download:
            return

        if item.qt_download.isPaused():
            item.state = "paused"
            item.speed_bps = 0
            item.eta_seconds = 0
        elif item.state == "paused":
            item.state = "in_progress"

        self.downloads_changed.emit()
        self._save_to_disk()

    def _on_state_changed(self, item_id: str, state) -> None:
        item = self._downloads.get(item_id)
        if not item:
            return

        st = QWebEngineDownloadRequest.DownloadState
        if state == st.DownloadCompleted:
            item.state = "completed"
            item.end_time = time.time()
            if item.total_bytes <= 0 and item.received_bytes > 0:
                item.total_bytes = item.received_bytes
            item.qt_download = None
            self.download_finished.emit(item.to_dict())
        elif state == st.DownloadCancelled:
            item.state = "cancelled"
            item.end_time = time.time()
            item.qt_download = None
            self.download_finished.emit(item.to_dict())
        elif state == st.DownloadInterrupted:
            item.state = "interrupted"
            item.end_time = time.time()
            if item.qt_download:
                item.error_message = item.qt_download.interruptReasonString()
            item.qt_download = None
            self.download_finished.emit(item.to_dict())
        elif state == st.DownloadInProgress:
            if item.qt_download and item.qt_download.isPaused():
                item.state = "paused"
            else:
                item.state = "in_progress"

        self._save_to_disk()
        self.downloads_changed.emit()

    # -----------------------------------------------------------------------
    # Public Control APIs
    # -----------------------------------------------------------------------
    def get_downloads(self) -> List[Dict[str, Any]]:
        """Returns all downloads sorted by start_time descending."""
        items = sorted(self._downloads.values(), key=lambda x: x.start_time, reverse=True)
        return [i.to_dict() for i in items]

    def get_active_count(self) -> int:
        """Returns count of active (in_progress or paused) downloads."""
        return sum(1 for i in self._downloads.values() if i.state in ("in_progress", "paused"))

    def pause(self, item_id: str) -> bool:
        item = self._downloads.get(item_id)
        if item and item.qt_download and item.state == "in_progress":
            item.qt_download.pause()
            item.state = "paused"
            self.downloads_changed.emit()
            self._save_to_disk()
            return True
        return False

    def resume(self, item_id: str) -> bool:
        item = self._downloads.get(item_id)
        if item and item.qt_download and item.state == "paused":
            item.qt_download.resume()
            item.state = "in_progress"
            self.downloads_changed.emit()
            self._save_to_disk()
            return True
        return False

    def cancel(self, item_id: str) -> bool:
        item = self._downloads.get(item_id)
        if item and item.qt_download and item.state in ("in_progress", "paused"):
            item.qt_download.cancel()
            item.state = "cancelled"
            item.end_time = time.time()
            item.qt_download = None
            self.downloads_changed.emit()
            self._save_to_disk()
            return True
        return False

    def open_file(self, item_id: str) -> bool:
        item = self._downloads.get(item_id)
        if not item or not os.path.exists(item.filepath):
            return False

        try:
            if sys.platform == "win32":
                os.startfile(item.filepath)
                return True
            else:
                return QDesktopServices.openUrl(QUrl.fromLocalFile(item.filepath))
        except Exception:
            return False

    def show_in_folder(self, item_id: str) -> bool:
        item = self._downloads.get(item_id)
        if not item or not os.path.exists(item.filepath):
            # If specific file is missing, open download directory
            return self.open_downloads_folder()

        try:
            if sys.platform == "win32":
                norm = os.path.normpath(item.filepath)
                subprocess.Popen(f'explorer /select,"{norm}"')
                return True
            else:
                folder = str(Path(item.filepath).parent)
                return QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        except Exception:
            return False

    def open_downloads_folder(self) -> bool:
        folder = str(self.get_download_directory())
        try:
            if sys.platform == "win32":
                os.startfile(folder)
                return True
            else:
                return QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        except Exception:
            return False

    def remove(self, item_id: str) -> bool:
        """Removes the download entry from history (does not delete file on disk)."""
        item = self._downloads.pop(item_id, None)
        if item:
            if item.qt_download and item.state in ("in_progress", "paused"):
                try:
                    item.qt_download.cancel()
                except Exception:
                    pass
            self._save_to_disk()
            self.downloads_changed.emit()
            return True
        return False

    def delete_file(self, item_id: str) -> bool:
        """Removes the download entry from history AND deletes the file on disk."""
        item = self._downloads.pop(item_id, None)
        if item:
            if item.qt_download and item.state in ("in_progress", "paused"):
                try:
                    item.qt_download.cancel()
                except Exception:
                    pass
            try:
                p = Path(item.filepath)
                if p.exists() and p.is_file():
                    p.unlink(missing_ok=True)
            except Exception:
                pass
            self._save_to_disk()
            self.downloads_changed.emit()
            return True
        return False

    def clear_completed(self) -> int:
        """Removes all finished (completed, cancelled, interrupted) downloads from history."""
        to_remove = [k for k, v in self._downloads.items() if v.state in ("completed", "cancelled", "interrupted")]
        for k in to_remove:
            self._downloads.pop(k, None)
        if to_remove:
            self._save_to_disk()
            self.downloads_changed.emit()
        return len(to_remove)

    def clear_all(self) -> int:
        """Clears all downloads from list."""
        count = self.clear_completed()
        return count

    # -----------------------------------------------------------------------
    # Disk Persistence
    # -----------------------------------------------------------------------
    def _save_to_disk(self) -> None:
        try:
            DOWNLOADS_FILE.parent.mkdir(parents=True, exist_ok=True)
            records = []
            for item in self._downloads.values():
                records.append({
                    "id": item.id,
                    "filename": item.filename,
                    "filepath": item.filepath,
                    "url": item.url,
                    "mime_type": item.mime_type,
                    "total_bytes": item.total_bytes,
                    "received_bytes": item.received_bytes,
                    "state": item.state if item.state != "in_progress" else "interrupted",
                    "start_time": item.start_time,
                    "end_time": item.end_time,
                    "error_message": item.error_message,
                })
            with open(DOWNLOADS_FILE, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except Exception:
            pass

    def _load_from_disk(self) -> None:
        if not DOWNLOADS_FILE.exists():
            return
        try:
            with open(DOWNLOADS_FILE, "r", encoding="utf-8") as f:
                records = json.load(f)
            for r in records:
                # Any previous uncompleted download is marked interrupted
                state = r.get("state", "completed")
                if state in ("in_progress", "paused"):
                    state = "interrupted"

                item = DownloadItem(
                    item_id=r.get("id", uuid.uuid4().hex[:12]),
                    filename=r.get("filename", "download"),
                    filepath=r.get("filepath", ""),
                    url=r.get("url", ""),
                    mime_type=r.get("mime_type", ""),
                    total_bytes=r.get("total_bytes", -1),
                    received_bytes=r.get("received_bytes", 0),
                    state=state,
                    start_time=r.get("start_time"),
                    end_time=r.get("end_time"),
                    error_message=r.get("error_message", ""),
                )
                self._downloads[item.id] = item
        except Exception:
            pass
