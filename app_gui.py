import tkinter as tk
from gui.theme import get_theme
from gui.result_panel import ResultPanel
from gui.query_panel import QueryPanel


class TopBar(tk.Frame):
    def __init__(self, master, on_open_settings=None):
        theme = get_theme()
        super().__init__(master, bg=theme["panel"], height=48)
        self.pack_propagate(False)

        title = tk.Label(
            self,
            text="📰 News Desk",
            bg=theme["panel"],
            fg=theme["fg"],
            font=("Segoe UI", 12, "bold"),
        )
        title.pack(side="left", padx=12)

        btn = tk.Button(
            self,
            text="⚙ Settings",
            command=on_open_settings or (lambda: None),
            relief="flat",
            bg=theme["button"],
            fg=theme["fg"],
            activebackground=theme["border"],
            activeforeground=theme["fg"],
            padx=12,
            pady=6,
        )
        btn.pack(side="right", padx=12)


class App:
    def __init__(self, root):
        self.root = root
        self.build()

    def build(self):
        theme = get_theme()
        self.root.title("News System")
        self.root.geometry("1100x680")
        self.root.configure(bg=theme["bg"])

        # 顶栏
        top = TopBar(self.root, on_open_settings=self.open_settings)
        top.pack(side="top", fill="x")

        # 主体容器
        body = tk.Frame(self.root, bg=theme["bg"])
        body.pack(side="top", fill="both", expand=True)

        # 先创建右侧结果，再创建左侧查询（但 pack 顺序：左 -> 右）
        self.result_panel = ResultPanel(body)
        self.query_panel = QueryPanel(body, self.result_panel)

        self.query_panel.pack(side="left", fill="y")
        self.result_panel.pack(side="right", fill="both", expand=True)

    def open_settings(self):
        # 先占位，后面 Day 8B-3 做完整设置面板
        win = tk.Toplevel(self.root)
        theme = get_theme()
        win.title("Settings")
        win.configure(bg=theme["bg"])
        win.geometry("420x320")
        tk.Label(win, text="Settings (Coming soon)", bg=theme["bg"], fg=theme["fg"]).pack(padx=20, pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
