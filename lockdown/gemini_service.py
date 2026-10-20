"""Gemini AI Service for Lock Down Browser.
Provides multimodal visual reasoning, page analysis, and instant problem solving
linked to the user's Gemini account.
"""

import base64
import json
import os
from typing import Any, Dict, List, Optional, Tuple

import httpx
from lockdown.config import load_settings, save_settings
from lockdown.qt_compat import QBuffer, QIODevice, QPixmap, QThread, pyqtSignal

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-2.5-flash"
SUPPORTED_MODELS = [
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash (Fastest & Multimodal)", "tag": "Recommended"},
    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash (Low Latency)", "tag": "Stable"},
    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro (Deep Reasoning)", "tag": "Pro"},
]


class GeminiService:
    """Manages Gemini account linkage, validation, and visual reasoning requests."""

    _instance: Optional["GeminiService"] = None

    def __init__(self):
        self.settings = load_settings()

    @classmethod
    def get_instance(cls) -> "GeminiService":
        if cls._instance is None:
            cls._instance = GeminiService()
        return cls._instance

    def get_api_key(self) -> str:
        s = load_settings()
        key = s.get("gemini_api_key", "").strip()
        if not key:
            key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not key:
            key = os.environ.get("GOOGLE_API_KEY", "").strip()
        return key

    def set_api_key(self, key: str) -> None:
        s = load_settings()
        s["gemini_api_key"] = key.strip()
        save_settings(s)

    def is_linked(self) -> bool:
        return bool(self.get_api_key())

    def get_model(self) -> str:
        s = load_settings()
        return s.get("gemini_model", DEFAULT_MODEL)

    def set_model(self, model: str) -> None:
        s = load_settings()
        s["gemini_model"] = model
        save_settings(s)

    def validate_api_key(self, api_key: str) -> Tuple[bool, str, List[str]]:
        """Tests an API key against Google Generative Language API.
        Returns: (is_valid, message, available_models)
        """
        key = api_key.strip()
        if not key:
            return False, "Please enter a valid Gemini API Key.", []

        url = f"{GEMINI_API_BASE}/models?key={key}"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    models = [
                        m.get("name", "").replace("models/", "")
                        for m in data.get("models", [])
                        if "generateContent" in m.get("supportedGenerationMethods", [])
                    ]
                    return True, "Successfully connected to your Gemini Account!", models
                else:
                    try:
                        err_data = res.json()
                        msg = err_data.get("error", {}).get("message", res.text)
                    except Exception:
                        msg = res.text
                    return False, f"Gemini API Error: {msg}", []
        except Exception as e:
            return False, f"Network error connecting to Gemini: {str(e)}", []

    def capture_viewport(self, tab_view) -> Tuple[Optional[QPixmap], str]:
        """Captures a high-resolution screenshot of the visible QWebEngineView.
        Returns: (QPixmap, base64_png_string)
        """
        if not tab_view:
            return None, ""

        try:
            pixmap = tab_view.grab()
            if pixmap.isNull():
                return None, ""

            buf = QBuffer()
            mode = getattr(QIODevice, "WriteOnly", None)
            if mode is None and hasattr(QIODevice, "OpenModeFlag"):
                mode = QIODevice.OpenModeFlag.WriteOnly
            buf.open(mode)
            pixmap.save(buf, "PNG")
            raw_bytes = buf.data().data()
            b64_str = base64.b64encode(raw_bytes).decode("ascii")
            return pixmap, b64_str
        except Exception as e:
            print(f"[GeminiService] Error capturing viewport: {e}")
            return None, ""

    def query(
        self,
        prompt: str,
        image_base64: str = "",
        page_url: str = "",
        page_title: str = "",
        page_text: str = "",
        selected_text: str = "",
    ) -> Dict[str, Any]:
        """Synchronously calls Gemini generateContent endpoint.
        Used inside worker thread.
        """
        api_key = self.get_api_key()
        if not api_key:
            raise ValueError(
                "Gemini account is not linked. Please provide your Gemini API Key in AI Mode settings."
            )

        model = self.get_model()
        url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={api_key}"

        # Build parts
        parts = []

        # System / Context preamble
        context_parts = []
        if page_title or page_url:
            context_parts.append(f"CURRENT WEBPAGE: '{page_title}' ({page_url})")
        if selected_text:
            context_parts.append(f"USER HIGHLIGHTED TEXT:\n\"\"\"{selected_text}\"\"\"")
        if page_text:
            snippet = page_text[:4000].strip()
            if snippet:
                context_parts.append(f"PAGE TEXT EXCERPT:\n\"\"\"{snippet}\"\"\"")

        system_instruction = (
            "You are Lock Down AI, an intelligent browser assistant embedded inside Lock Down Browser. "
            "You are observing the user's active browser viewport. Provide direct, highly actionable solutions. "
            "When helping with errors or coding, write clean code snippets with explanations. "
            "Format your answer with clear markdown headings, lists, and code blocks."
        )

        full_prompt = prompt
        if context_parts:
            full_prompt = "\n\n".join(context_parts) + f"\n\nUSER REQUEST / QUESTION:\n{prompt}"

        parts.append({"text": full_prompt})

        # Multimodal image attachment
        if image_base64:
            parts.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": image_base64,
                }
            })

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": parts,
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 4096,
            },
        }

        with httpx.Client(timeout=35.0) as client:
            res = client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
            )

            if res.status_code != 200:
                try:
                    err_msg = res.json().get("error", {}).get("message", res.text)
                except Exception:
                    err_msg = res.text
                raise RuntimeError(f"Gemini API Error ({res.status_code}): {err_msg}")

            data = res.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("No response candidate returned by Gemini.")

            content_parts = candidates[0].get("content", {}).get("parts", [])
            text_result = "".join(p.get("text", "") for p in content_parts)

            return {
                "text": text_result,
                "model": model,
                "has_image": bool(image_base64),
                "prompt": prompt,
            }


class GeminiQueryWorker(QThread):
    """Background worker thread so UI never hangs while querying Gemini."""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(
        self,
        prompt: str,
        image_base64: str = "",
        page_url: str = "",
        page_title: str = "",
        page_text: str = "",
        selected_text: str = "",
    ):
        super().__init__()
        self.prompt = prompt
        self.image_base64 = image_base64
        self.page_url = page_url
        self.page_title = page_title
        self.page_text = page_text
        self.selected_text = selected_text

    def run(self):
        try:
            service = GeminiService.get_instance()
            result = service.query(
                prompt=self.prompt,
                image_base64=self.image_base64,
                page_url=self.page_url,
                page_title=self.page_title,
                page_text=self.page_text,
                selected_text=self.selected_text,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
