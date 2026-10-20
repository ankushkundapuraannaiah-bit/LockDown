"""Local Flask server for the Lock Down home page, extensions hub, and media assets."""

import queue
import threading
from pathlib import Path
from typing import Callable, Optional

from flask import Flask, Response, abort, jsonify, request, send_file
from werkzeug.serving import make_server

from lockdown.config import BASE_DIR, load_settings, save_settings
from lockdown.download_manager import DownloadManager
from lockdown.downloads_page import generate_downloads_html
from lockdown.extension_manager import ExtensionManager
from lockdown.extensions_page import generate_extensions_html
from lockdown.gemini_service import GeminiService
from lockdown.homepage import generate_home_html
from lockdown.settings_page import generate_settings_html


class HomeServer:
    _instance: Optional["HomeServer"] = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self.app = Flask(__name__)
        self.server = None
        self.thread = None
        self.base_url = ""
        self.browse_folder_callback: Optional[Callable[[], Optional[str]]] = None
        self._configure_routes()

    @classmethod
    def get_instance(cls) -> "HomeServer":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = HomeServer()
                cls._instance.start()
            return cls._instance

    def set_browse_folder_callback(self, cb: Callable[[], Optional[str]]) -> None:
        self.browse_folder_callback = cb

    def _configure_routes(self) -> None:
        @self.app.after_request
        def add_cache_headers(response):
            if response.content_type.startswith("text/html"):
                response.headers["Cache-Control"] = "no-store, max-age=0"
            return response

        @self.app.get("/api/suggestions")
        def suggestions_api():
            from lockdown.suggestions import fetch_search_suggestions
            q = request.args.get("q", "")
            engine = request.args.get("engine", "Google")
            results = fetch_search_suggestions(q, engine)
            return jsonify(results)

        @self.app.get("/lockdown-home")
        def lockdown_home():
            storage_mode = (
                "Server (Google Drive)"
                if load_settings().get("history_storage_mode") == "gdrive"
                else "Local Secure Vault"
            )
            html = generate_home_html(
                storage_mode=storage_mode,
                asset_base_url=self.base_url,
            )
            return Response(html, mimetype="text/html")

        # -------------------------------------------------------------------
        # EXTENSIONS PAGE & APIS
        # -------------------------------------------------------------------
        @self.app.get("/lockdown-extensions")
        def lockdown_extensions():
            mgr = ExtensionManager.get_instance()
            html = generate_extensions_html(
                installed=mgr.get_installed(),
                library=mgr.get_library(),
                asset_base_url=self.base_url,
            )
            return Response(html, mimetype="text/html")

        @self.app.get("/api/extensions/list")
        def extensions_list_api():
            mgr = ExtensionManager.get_instance()
            return jsonify({
                "installed": mgr.get_installed(),
                "library": mgr.get_library(),
            })

        @self.app.post("/api/extensions/toggle")
        def extensions_toggle_api():
            data = request.get_json(silent=True) or {}
            ext_id = data.get("id", "")
            enabled = data.get("enabled", True)
            mgr = ExtensionManager.get_instance()
            success = mgr.set_enabled(ext_id, enabled)
            return jsonify({"success": success})

        @self.app.post("/api/extensions/install")
        def extensions_install_api():
            data = request.get_json(silent=True) or {}
            ext_id = data.get("id", "")
            mgr = ExtensionManager.get_instance()
            success = mgr.install_from_library(ext_id)
            name = ext_id.title()
            for item in mgr.get_library():
                if item["id"] == ext_id:
                    name = item["name"]
                    break
            return jsonify({"success": success, "name": name})

        @self.app.post("/api/extensions/uninstall")
        def extensions_uninstall_api():
            data = request.get_json(silent=True) or {}
            ext_id = data.get("id", "")
            mgr = ExtensionManager.get_instance()
            success = mgr.uninstall(ext_id)
            return jsonify({"success": success})

        @self.app.post("/api/extensions/browse_folder")
        def extensions_browse_folder_api():
            data = request.get_json(silent=True) or {}
            folder_path = data.get("path")
            if not folder_path and self.browse_folder_callback:
                folder_path = self.browse_folder_callback()

            if not folder_path:
                return jsonify({"success": False, "error": "Cancelled"})

            mgr = ExtensionManager.get_instance()
            res = mgr.install_unpacked(folder_path)
            if res:
                return jsonify({"success": True, "name": res.get("name", "Extension")})
            return jsonify({"success": False, "error": "Invalid extension folder (missing manifest.json)"})

        @self.app.post("/api/extensions/download_online")
        def extensions_download_online_api():
            data = request.get_json(silent=True) or {}
            url = data.get("url", "").strip()
            ext_id = data.get("id", "").strip()
            mgr = ExtensionManager.get_instance()
            ok, meta, msg = mgr.download_and_install_from_url(url=url, ext_id=ext_id)
            if ok and meta:
                return jsonify({
                    "success": True,
                    "name": meta.get("name", ext_id or "Extension"),
                    "message": msg,
                    "extension": meta,
                })
            return jsonify({"success": False, "error": msg or "Download failed"})

        # -------------------------------------------------------------------
        # SETTINGS PAGE & APIS
        # -------------------------------------------------------------------
        @self.app.get("/lockdown-settings")
        def lockdown_settings():
            settings = load_settings()
            html = generate_settings_html(
                settings=settings,
                asset_base_url=self.base_url,
            )
            return Response(html, mimetype="text/html")

        @self.app.get("/api/settings/get")
        def settings_get_api():
            return jsonify(load_settings())

        @self.app.post("/api/settings/save")
        def settings_save_api():
            data = request.get_json(silent=True) or {}
            current = load_settings()
            current.update(data)
            save_settings(current)
            return jsonify({"success": True})

        @self.app.post("/api/settings/verify_gemini")
        def settings_verify_gemini_api():
            data = request.get_json(silent=True) or {}
            api_key = data.get("api_key", "").strip()
            if not api_key:
                return jsonify({"valid": False, "message": "API key cannot be empty"})
            try:
                service = GeminiService.get_instance()
                valid, message, models = service.validate_api_key(api_key)
                if valid:
                    return jsonify({
                        "valid": True,
                        "message": message,
                        "models": models,
                    })
                return jsonify({"valid": False, "message": message})
            except Exception as e:
                return jsonify({"valid": False, "message": str(e)})

        # -------------------------------------------------------------------
        # DOWNLOADS PAGE & APIS
        # -------------------------------------------------------------------
        @self.app.get("/lockdown-downloads")
        def lockdown_downloads():
            html = generate_downloads_html(asset_base_url=self.base_url)
            return Response(html, mimetype="text/html")

        @self.app.get("/api/downloads/list")
        def downloads_list_api():
            mgr = DownloadManager.get_instance()
            return jsonify({
                "downloads": mgr.get_downloads(),
                "active_count": mgr.get_active_count(),
                "directory": str(mgr.get_download_directory()),
            })

        @self.app.post("/api/downloads/pause")
        def downloads_pause_api():
            data = request.get_json(silent=True) or {}
            item_id = data.get("id", "")
            return jsonify({"success": DownloadManager.get_instance().pause(item_id)})

        @self.app.post("/api/downloads/resume")
        def downloads_resume_api():
            data = request.get_json(silent=True) or {}
            item_id = data.get("id", "")
            return jsonify({"success": DownloadManager.get_instance().resume(item_id)})

        @self.app.post("/api/downloads/cancel")
        def downloads_cancel_api():
            data = request.get_json(silent=True) or {}
            item_id = data.get("id", "")
            return jsonify({"success": DownloadManager.get_instance().cancel(item_id)})

        @self.app.post("/api/downloads/open")
        def downloads_open_api():
            data = request.get_json(silent=True) or {}
            item_id = data.get("id", "")
            return jsonify({"success": DownloadManager.get_instance().open_file(item_id)})

        @self.app.post("/api/downloads/show_in_folder")
        def downloads_show_in_folder_api():
            data = request.get_json(silent=True) or {}
            item_id = data.get("id", "")
            return jsonify({"success": DownloadManager.get_instance().show_in_folder(item_id)})

        @self.app.post("/api/downloads/open_folder")
        def downloads_open_folder_api():
            return jsonify({"success": DownloadManager.get_instance().open_downloads_folder()})

        @self.app.post("/api/downloads/remove")
        def downloads_remove_api():
            data = request.get_json(silent=True) or {}
            item_id = data.get("id", "")
            return jsonify({"success": DownloadManager.get_instance().remove(item_id)})

        @self.app.post("/api/downloads/delete_file")
        def downloads_delete_file_api():
            data = request.get_json(silent=True) or {}
            item_id = data.get("id", "")
            return jsonify({"success": DownloadManager.get_instance().delete_file(item_id)})

        @self.app.post("/api/downloads/clear_completed")
        def downloads_clear_completed_api():
            count = DownloadManager.get_instance().clear_completed()
            return jsonify({"success": True, "count": count})

        # -------------------------------------------------------------------
        # MEDIA ASSETS
        # -------------------------------------------------------------------
        @self.app.get("/assets/wallpaper.webm")
        def wallpaper_webm():
            path = BASE_DIR / "wallpaper.webm"
            if not path.exists():
                abort(404)
            return send_file(path, mimetype="video/webm", conditional=True)

        @self.app.get("/assets/wallpaper.mp4")
        def wallpaper_video():
            path = BASE_DIR / "wallpaper.mp4"
            if not path.exists():
                abort(404)
            return send_file(path, mimetype="video/mp4", conditional=True)

        @self.app.get("/assets/wallpaper_frames/<path:filename>")
        def wallpaper_frame(filename: str):
            frames_dir = (BASE_DIR / "wallpaper_frames").resolve()
            path = (frames_dir / filename).resolve()
            if frames_dir not in path.parents or not path.exists() or path.suffix.lower() != ".jpg":
                abort(404)
            return send_file(path, mimetype="image/jpeg", conditional=True)

    def start(self) -> None:
        if self.server:
            return
        self.server = make_server("127.0.0.1", 0, self.app, threaded=True)
        port = self.server.server_port
        self.base_url = f"http://127.0.0.1:{port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def home_url(self) -> str:
        return f"{self.base_url}/lockdown-home"

    def extensions_url(self) -> str:
        return f"{self.base_url}/lockdown-extensions"

    def settings_url(self) -> str:
        return f"{self.base_url}/lockdown-settings"

    def downloads_url(self) -> str:
        return f"{self.base_url}/lockdown-downloads"


def get_home_url() -> str:
    return HomeServer.get_instance().home_url()


def get_extensions_url() -> str:
    return HomeServer.get_instance().extensions_url()


def get_settings_url() -> str:
    return HomeServer.get_instance().settings_url()


def get_downloads_url() -> str:
    return HomeServer.get_instance().downloads_url()
