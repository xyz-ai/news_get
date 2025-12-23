import tkinter as tk
from gui.theme import get_theme
from core.settings import AppSettings
from core.query_engine import query_news
from gui.i18n import t


class QueryPanel(tk.Frame):
    def __init__(self, master, result_panel):
        theme = get_theme()
        super().__init__(master, bg=theme["panel"], width=260)
        self.pack_propagate(False)

        self.result_panel = result_panel

        # ── Title ─────────────────────────────
        self.lbl_title = tk.Label(self)
        self.lbl_title.pack(anchor="w", padx=12, pady=(10, 6))

        # ── Keyword ───────────────────────────
        self.lbl_kw = tk.Label(self)
        self.lbl_kw.pack(anchor="w", padx=12)

        self.keyword = tk.Entry(self, relief="flat")
        self.keyword.pack(fill="x", padx=12, pady=(4, 10))
        self.keyword.insert(0, AppSettings.default_keyword)

        # ── Search Button ─────────────────────
        self.btn_search = tk.Button(
            self,
            command=self.search,
            relief="flat",
            padx=10,
            pady=6,
        )
        self.btn_search.pack(fill="x", padx=12, pady=(0, 10))

        # ── Hint (future filters) ─────────────
        self.lbl_hint = tk.Label(
            self,
            justify="left",
            wraplength=220,
        )
        self.lbl_hint.pack(anchor="w", padx=12, pady=(0, 10))

        # ── Panel Width Slider ─────────────────
        self.lbl_width = tk.Label(self)
        self.lbl_width.pack(anchor="w", padx=12)

        self.width_scale = tk.Scale(
            self,
            from_=220,
            to=420,
            orient="horizontal",
            showvalue=True,
            command=self.on_width_change,
            highlightthickness=0,
        )
        self.width_scale.set(260)
        self.width_scale.pack(fill="x", padx=12, pady=(0, 12))

        # 初次应用主题 / 文案
        self.apply_theme()

    # ────────────────────────────────────────
    # Theme / Language Refresh
    # ────────────────────────────────────────
    def apply_theme(self):
        theme = get_theme()
        fs = AppSettings.font_size

        self.config(bg=theme["panel"])

        self.lbl_title.config(
            text=t("query"),
            bg=theme["panel"],
            fg=theme["fg"],
            font=("Segoe UI", fs, "bold"),
        )

        self.lbl_kw.config(
            text=t("keyword"),
            bg=theme["panel"],
            fg=theme["muted"],
            font=("Segoe UI", fs - 1),
        )

        self.keyword.config(
            bg=theme["bg"],
            fg=theme["fg"],
            insertbackground=theme["fg"],
            font=("Segoe UI", fs),
        )

        self.btn_search.config(
            text=t("search"),
            bg=theme["button"],
            fg=theme["fg"],
            activebackground=theme["border"],
            activeforeground=theme["fg"],
            font=("Segoe UI", fs),
        )

        self.lbl_hint.config(
            text=t("query_hint"),
            bg=theme["panel"],
            fg=theme["muted"],
            font=("Segoe UI", fs - 2),
        )

        self.lbl_width.config(
            text=t("panel_width"),
            bg=theme["panel"],
            fg=theme["muted"],
            font=("Segoe UI", fs - 2),
        )

        self.width_scale.config(
            bg=theme["panel"],
            fg=theme["fg"],
            troughcolor=theme["bg"],
            font=("Segoe UI", fs - 2),
        )

    # ────────────────────────────────────────
    # Actions
    # ────────────────────────────────────────
    def on_width_change(self, v):
        self.config(width=int(float(v)))

    def search(self):
        keyword = self.keyword.get().strip()
        print("DEBUG search keyword =", repr(keyword))

        rows = []

        try:
            rows = query_news(keyword=keyword)
        except Exception as e:
            print("ERROR query_news failed:", e)
            rows = []

        print("DEBUG QueryPanel.search rows =", rows)
        self.result_panel.load(rows)


    def sync_defaults(self):
        self.keyword.delete(0, "end")
        self.keyword.insert(0, AppSettings.default_keyword)
