# app_gui.py 顶部
#print(">>> importing ResultPanel")

#print(">>> imported ResultPanel")

import tkinter as tk
import threading

from gui.theme import get_theme
from core.settings import AppSettings
from core.translator import translate_en_zh
from core.article_repo import (
    get_article_by_link,
    save_article_en,
    save_article_zh,
)
from core.article_fetcher import fetch_article_content


class ResultPanel(tk.Frame):
    def __init__(self, master):
        #print(">>> ResultPanel init start")

        self.theme = get_theme()
        #print(">>> theme loaded")

        super().__init__(master, bg=self.theme["bg"])
        #print(">>> tk.Frame init ok")

        self.data = []
        #print(">>> ResultPanel init end")

        self.current_article = None

        # ───────── 左侧：新闻列表 ─────────
        left = tk.Frame(self, bg=self.theme["panel"], width=360)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        self.listbox = tk.Listbox(
            left,
            bg=self.theme["panel"],
            fg=self.theme["fg"],
            selectbackground=self.theme["accent"],
        )
        self.listbox.pack(fill="both", expand=True, padx=8, pady=8)

        self.listbox.bind("<<ListboxSelect>>", self.show_detail)

        # ───────── 右侧：正文区域 ─────────
        right = tk.Frame(self, bg=self.theme["bg"])
        right.pack(side="right", fill="both", expand=True)

        self.text = tk.Text(
            right,
            bg=self.theme["bg"],
            fg=self.theme["fg"],
            wrap="word",
        )
        self.text.pack(fill="both", expand=True, padx=12, pady=12)

        self.text.tag_config("title", font=("Segoe UI", 14, "bold"))

    # ===============================
    # 列表加载（UI线程）
    # ===============================
    def load(self, rows):
        self.data = rows or []
        self.listbox.delete(0, tk.END)

        for r in self.data:
            self.listbox.insert(tk.END, r[0])

    # ===============================
    # 点击新闻（UI线程）
    # ===============================
    def show_detail(self, _):
        if not self.listbox.curselection():
            return

        idx = self.listbox.curselection()[0]
        title, source, region, published, link = self.data[idx]

        # 立即反馈 UI（非常关键）
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, title + "\n\n", "title")
        self.text.insert(tk.END, "Loading article...\n")

        # 启动后台线程
        threading.Thread(
            target=self._load_article_bg,
            args=(title, link),
            daemon=True,
        ).start()

    # ===============================
    # 后台线程：抓正文 + 翻译 + 存库
    # ===============================
    def _load_article_bg(self, title, link):
        # 1️⃣ 先查数据库
        article = get_article_by_link(link)

        content_en = ""
        content_zh = ""

        if article:
            content_en = article.get("content_en") or ""
            content_zh = article.get("content_zh") or ""

        # 2️⃣ 没英文正文 → 抓
        if not content_en:
            try:
                content_en = fetch_article_content(link)
                save_article_en(link, content_en)
            except Exception as e:
                content_en = f"[Failed to fetch article: {e}]"

        # 3️⃣ 需要翻译 & 没中文 → 翻一次
        if AppSettings.auto_translate and not content_zh and content_en:
            try:
                content_zh = translate_en_zh(content_en)
                save_article_zh(link, content_zh)
            except Exception as e:
                content_zh = f"[Translation failed: {e}]"

        # 4️⃣ 回到 UI 线程渲染
        self.after(
            0,
            lambda: self._render_article(title, content_en, content_zh, link)
        )

    # ===============================
    # UI线程：真正显示正文
    # ===============================
    def _render_article(self, title, en, zh, link):
        mode = AppSettings.translate_mode

        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, title + "\n\n", "title")

        if mode == "en_zh":
            self.text.insert(tk.END, en + "\n\n")
            if zh:
                self.text.insert(tk.END, zh + "\n")

        elif mode == "zh_only":
            self.text.insert(tk.END, zh or "[No Chinese translation]\n")

        elif mode == "zh_en":
            if zh:
                self.text.insert(tk.END, zh + "\n\n")
            self.text.insert(tk.END, en + "\n")

        else:
            self.text.insert(tk.END, en + "\n")

        self.text.insert(tk.END, "\n🔗 " + link)
