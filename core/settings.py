# core/settings.py
import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent / "settings.json"


class AppSettings:
    # ── Appearance ─────────────────
    theme = "dark"        # dark / light
    language = "zh"       # zh / en
    font_size = 12        # 10 ~ 16

    # ── Behavior ───────────────────
    # 翻译显示模式
    # "en_zh" | "zh_only" | "zh_en"
    translate_mode = "en_zh"
    auto_translate = True
    # ── Default query params ───────
    default_keyword = ""
    default_days = 2
    default_source = "ALL"


# ──────────────────────────────
# Persistence
# ──────────────────────────────

def load_settings():
    if not SETTINGS_FILE.exists():
        return

    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        for k, v in data.items():
            if hasattr(AppSettings, k):
                setattr(AppSettings, k, v)
    except Exception:
        pass


def save_settings():
    data = {
        k: getattr(AppSettings, k)
        for k in vars(AppSettings)
        if not k.startswith("_") and not callable(getattr(AppSettings, k))
    }
    SETTINGS_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ──────────────────────────────
# Helpers
# ──────────────────────────────

def toggle_theme():
    AppSettings.theme = "light" if AppSettings.theme == "dark" else "dark"
    save_settings()


def toggle_language():
    AppSettings.language = "en" if AppSettings.language == "zh" else "zh"
    save_settings()


def set_font_size(size: int):
    if 10 <= size <= 16:
        AppSettings.font_size = size
        save_settings()
