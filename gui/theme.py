# gui/theme.py
from core.settings import AppSettings

DARK = {
    "bg": "#121212",
    "panel": "#1e1e1e",
    "fg": "#eeeeee",
    "button": "#2a2a2a",
    "border": "#333333",
    "accent": "#4ea1ff",
    "muted": "#9aa0b4", 
}

LIGHT = {
    "bg": "#f5f5f5",
    "panel": "#ffffff",
    "fg": "#222222",
    "button": "#e6e6e6",
    "border": "#cccccc",
    "accent": "#0078d4",
    "muted": "#6b7280",
}

def get_theme():
    return DARK if AppSettings.theme == "dark" else LIGHT
