import tkinter as tk
from gui.theme import get_theme
from core.query_engine import query_news


class QueryPanel(tk.Frame):
    def __init__(self, master, result_panel):
        theme = get_theme()
        super().__init__(master, bg=theme["panel"], width=260)
        self.pack_propagate(False)

        self.result_panel = result_panel
        self._theme = theme

        tk.Label(self, text="Query", bg=theme["panel"], fg=theme["fg"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        # 关键词
        tk.Label(self, text="Keyword", bg=theme["panel"], fg=theme["muted"]).pack(anchor="w", padx=12)
        self.keyword = tk.Entry(self, relief="flat")
        self.keyword.pack(fill="x", padx=12, pady=(4, 10))

        # 搜索按钮
        btn = tk.Button(
            self,
            text="Search",
            command=self.search,
            relief="flat",
            bg=theme["button"],
            fg=theme["fg"],
            activebackground=theme["border"],
            activeforeground=theme["fg"],
            padx=10,
            pady=6,
        )
        btn.pack(fill="x", padx=12, pady=(0, 10))

        # 占位：以后这里扩展复合查询参数（source/region/days/limit/AND OR NOT）
        hint = tk.Label(
            self,
            text="(More filters will be added here)",
            bg=theme["panel"],
            fg=theme["muted"],
            justify="left",
        )
        hint.pack(anchor="w", padx=12, pady=(0, 10))

        # ✅ 你要的“左右滚动轴”放在最下面：用来调整左面板宽度
        tk.Label(self, text="Panel Width", bg=theme["panel"], fg=theme["muted"]).pack(anchor="w", padx=12)
        self.width_scale = tk.Scale(
            self,
            from_=220,
            to=420,
            orient="horizontal",
            showvalue=True,
            command=self.on_width_change,
            bg=theme["panel"],
            fg=theme["fg"],
            highlightthickness=0,
            troughcolor=theme["bg"],
        )
        self.width_scale.set(260)
        self.width_scale.pack(fill="x", padx=12, pady=(0, 12))

    def on_width_change(self, v):
        self.config(width=int(float(v)))

    def search(self):
        rows = query_news(keyword=self.keyword.get().strip())
        self.result_panel.load(rows)
