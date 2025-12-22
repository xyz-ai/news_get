import tkinter as tk

from gui.theme import get_theme
from gui.query_panel import QueryPanel
from gui.result_panel import ResultPanel
from gui.i18n import t

from core.settings import (
    AppSettings,
    load_settings,
    save_settings,
    set_translate_mode,
)

# 启动时加载配置
load_settings()


# ─────────────────────────────────────
# Top Bar
# ─────────────────────────────────────
class TopBar(tk.Frame):
    def __init__(self, master, on_open_settings):
        super().__init__(master)
        self.on_open_settings = on_open_settings

        self.lbl_title = tk.Label(self)
        self.lbl_title.pack(side="left", padx=14)

        self.btn_settings = tk.Button(
            self,
            command=self.on_open_settings,
            relief="flat",
            padx=12,
            pady=6,
        )
        self.btn_settings.pack(side="right", padx=14)

        self.apply_theme()

    def apply_theme(self):
        theme = get_theme()
        fs = AppSettings.font_size

        self.config(bg=theme["panel"], height=48)
        self.pack_propagate(False)

        self.lbl_title.config(
            text=t("title"),
            bg=theme["panel"],
            fg=theme["fg"],
            font=("Segoe UI", fs, "bold"),
        )

        self.btn_settings.config(
            text="⚙ " + t("settings"),
            bg=theme["button"],
            fg=theme["fg"],
            activebackground=theme["border"],
            activeforeground=theme["fg"],
            font=("Segoe UI", fs),
        )


# ─────────────────────────────────────
# App
# ─────────────────────────────────────
class App:
    def __init__(self, root: tk.Tk):
        self.root = root

        self.topbar = None
        self.query_panel = None
        self.result_panel = None

        # Settings window (single instance)
        self.settings_win = None
        self.settings_kw = None
        self.settings_days = None
        self.settings_src = None

        self.build()

    # ──────────────────────────────
    # Build UI
    # ──────────────────────────────
    def build(self):
        theme = get_theme()

        self.root.title("News System")
        self.root.geometry("1100x680")
        self.root.configure(bg=theme["bg"])

        # Top bar
        self.topbar = TopBar(self.root, self.open_settings)
        self.topbar.pack(side="top", fill="x")

        # Body
        body = tk.Frame(self.root, bg=theme["bg"])
        body.pack(side="top", fill="both", expand=True)

        self.result_panel = ResultPanel(body)
        self.query_panel = QueryPanel(body, self.result_panel)

        self.query_panel.pack(side="left", fill="y")
        self.result_panel.pack(side="right", fill="both", expand=True)

    # ──────────────────────────────
    # Theme / Language Refresh
    # ──────────────────────────────
    def refresh_theme(self):
        theme = get_theme()
        self.root.configure(bg=theme["bg"])

        self.topbar.apply_theme()
        self.query_panel.apply_theme()
        self.result_panel.apply_theme()

    def toggle_theme(self):
        AppSettings.theme = "light" if AppSettings.theme == "dark" else "dark"
        save_settings()
        self.refresh_theme()

    # ──────────────────────────────
    # Settings Window
    # ──────────────────────────────
    def open_settings(self):
        # 单例保护
        if self.settings_win and self.settings_win.winfo_exists():
            self.settings_win.lift()
            self.refresh_settings_values()
            return

        theme = get_theme()
        fs = AppSettings.font_size

        self.settings_win = tk.Toplevel(self.root)
        win = self.settings_win
        win.title(t("settings"))
        win.geometry("420x600")
        win.configure(bg=theme["bg"])
        win.protocol("WM_DELETE_WINDOW", self.close_settings)

        # ── Appearance ─────────────────
        tk.Label(
            win,
            text=t("appearance"),
            bg=theme["bg"],
            fg=theme["fg"],
            font=("Segoe UI", fs, "bold"),
        ).pack(anchor="w", padx=20, pady=(20, 10))

        tk.Button(
            win,
            text=t("toggle_theme"),
            command=self.toggle_theme,
            relief="flat",
            bg=theme["button"],
            fg=theme["fg"],
        ).pack(anchor="w", padx=20)

        # ── Language ───────────────────
        tk.Label(
            win,
            text=t("language"),
            bg=theme["bg"],
            fg=theme["fg"],
            font=("Segoe UI", fs, "bold"),
        ).pack(anchor="w", padx=20, pady=(20, 6))

        lang_var = tk.StringVar(value=AppSettings.language)

        def change_lang():
            AppSettings.language = lang_var.get()
            save_settings()
            self.refresh_theme()
            self.result_panel.refresh_current()

        for txt, val in [("English", "en"), ("中文", "zh")]:
            tk.Radiobutton(
                win,
                text=txt,
                variable=lang_var,
                value=val,
                command=change_lang,
                bg=theme["bg"],
                fg=theme["fg"],
                selectcolor=theme["panel"],
            ).pack(anchor="w", padx=40)

        # ── Content Translation Mode ───
        tk.Label(
            win,
            text=t("translation_mode"),
            bg=theme["bg"],
            fg=theme["fg"],
            font=("Segoe UI", fs, "bold"),
        ).pack(anchor="w", padx=20, pady=(20, 6))

        mode_var = tk.StringVar(value=AppSettings.translate_mode)

        def change_translate_mode():
            set_translate_mode(mode_var.get())
            self.result_panel.refresh_current()

        for key in ["mode_en_zh", "mode_zh_only", "mode_zh_en"]:
            tk.Radiobutton(
                win,
                text=t(key),
                variable=mode_var,
                value=key.replace("mode_", ""),
                command=change_translate_mode,
                bg=theme["bg"],
                fg=theme["fg"],
                selectcolor=theme["panel"],
            ).pack(anchor="w", padx=40)

        # ── Default Query Params ─────────
        tk.Label(
            win,
            text=t("default_params"),
            bg=theme["bg"],
            fg=theme["fg"],
            font=("Segoe UI", fs, "bold"),
        ).pack(anchor="w", padx=20, pady=(20, 6))

        self.settings_kw = tk.Entry(win)
        self.settings_kw.pack(fill="x", padx=20, pady=4)

        self.settings_days = tk.Spinbox(win, from_=1, to=30)
        self.settings_days.pack(anchor="w", padx=20, pady=4)

        self.settings_src = tk.StringVar()
        tk.OptionMenu(
            win, self.settings_src, "ALL", "BBC", "Guardian", "Fox"
        ).pack(anchor="w", padx=20, pady=4)

        self.refresh_settings_values()

        # ── Save ──────────────────────
        tk.Button(
            win,
            text=t("save"),
            command=self.save_defaults,
            relief="flat",
            bg=theme["button"],
            fg=theme["fg"],
        ).pack(anchor="e", padx=20, pady=20)

    def refresh_settings_values(self):
        if not self.settings_kw:
            return
        self.settings_kw.delete(0, "end")
        self.settings_kw.insert(0, AppSettings.default_keyword)

        self.settings_days.delete(0, "end")
        self.settings_days.insert(0, AppSettings.default_days)

        self.settings_src.set(AppSettings.default_source)

    def save_defaults(self):
        AppSettings.default_keyword = self.settings_kw.get().strip()
        AppSettings.default_days = int(self.settings_days.get())
        AppSettings.default_source = self.settings_src.get()

        save_settings()
        self.query_panel.sync_defaults()

        self.close_settings()

    def close_settings(self):
        if self.settings_win:
            self.settings_win.destroy()
            self.settings_win = None


# ─────────────────────────────────────
# Main
# ─────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
