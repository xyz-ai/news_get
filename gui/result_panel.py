import tkinter as tk
from gui.theme import get_theme
from core.translator import translate


class ResultPanel(tk.Frame):
    def __init__(self, master):
        theme = get_theme()
        super().__init__(master, bg=theme["bg"])

        # 左：列表区域（带滚动条）
        left = tk.Frame(self, bg=theme["panel"], width=360)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="News List", bg=theme["panel"], fg=theme["fg"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 6))

        list_wrap = tk.Frame(left, bg=theme["panel"])
        list_wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.listbox = tk.Listbox(
            list_wrap,
            bg=theme["panel"],
            fg=theme["fg"],
            selectbackground=theme["accent"],
            highlightthickness=1,
            highlightbackground=theme["border"],
            relief="flat",
            activestyle="none",
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(list_wrap, command=self.listbox.yview)
        sb.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=sb.set)

        # 右：详情区域（带滚动条）
        right = tk.Frame(self, bg=theme["bg"])
        right.pack(side="right", fill="both", expand=True)

        tk.Label(right, text="Detail", bg=theme["bg"], fg=theme["fg"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(10, 6))

        text_wrap = tk.Frame(right, bg=theme["bg"])
        text_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.text = tk.Text(
            text_wrap,
            bg=theme["bg"],
            fg=theme["fg"],
            wrap="word",
            relief="flat",
            highlightthickness=1,
            highlightbackground=theme["border"],
        )
        self.text.pack(side="left", fill="both", expand=True)

        tsb = tk.Scrollbar(text_wrap, command=self.text.yview)
        tsb.pack(side="right", fill="y")
        self.text.config(yscrollcommand=tsb.set)

        # 数据 + 事件
        self.data = []
        self.listbox.bind("<<ListboxSelect>>", self.show_detail)

    def load(self, rows):
        """rows: [(title, source, region, published, link), ...]"""
        self.data = rows or []
        self.listbox.delete(0, tk.END)
        for r in self.data:
            self.listbox.insert(tk.END, r[0])

        # 自动显示第一条（提升体验）
        if self.data:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.activate(0)
            self.show_detail(None)

    def show_detail(self, _):
        if not self.listbox.curselection():
            return

        idx = self.listbox.curselection()[0]
        title, source, region, published, link = self.data[idx]

        zh = translate(title)

        self.text.delete("1.0", tk.END)

        self.text.insert(tk.END, title + "\n", "title")
        self.text.insert(tk.END, zh + "\n\n", "zh")

        self.text.insert(
            tk.END,
            "📄 Full article content not fetched yet.\n",
            "hint"
        )
        self.text.insert(
            tk.END,
            "🔗 Open original link:\n",
            "meta"
        )
        self.text.insert(tk.END, link + "\n", "link")

        self.text.tag_config("title", font=("Segoe UI", 14, "bold"))
        self.text.tag_config("zh", font=("Segoe UI", 12))
        self.text.tag_config("hint", foreground="#888888")
        self.text.tag_config("meta", foreground="#aaaaaa")
        self.text.tag_config("link", foreground="#4ea1ff", underline=True)

