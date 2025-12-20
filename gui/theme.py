THEMES = {
    "dark": {
        "bg": "#1e1e1e",
        "panel": "#252526",
        "fg": "#e5e5e5",
        "muted": "#9e9e9e",
        "button": "#333333",
        "accent": "#0a84ff",
        "border": "#3c3c3c",
    },
    "light": {
        "bg": "#f5f5f5",
        "panel": "#ffffff",
        "fg": "#1e1e1e",
        "muted": "#666666",
        "button": "#e0e0e0",
        "accent": "#0066cc",
        "border": "#cccccc",
    }
}

CURRENT_THEME = "dark"


def get_theme():
    return THEMES[CURRENT_THEME]


def set_theme(name):
    global CURRENT_THEME
    CURRENT_THEME = name
