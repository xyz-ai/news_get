import tkinter as tk
from threading import Thread

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
        theme = get_theme()
        super().__init__(master, bg=theme["bg"])

        self.theme = theme
        self.data = []                 # [(title, source, region, published, link)]
        self.current_article = None    # dict from DB

        # ───────── 左侧：新闻列表 ─────────
        left = tk.Frame(self, bg=theme["panel"], width=360)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        self.listbox = tk.Listbox(
            left,
            bg=theme["panel"],
            fg=theme["fg"],
            selectbackground=theme["accent"],
            highlightthickness=0,
            relief="flat",
        )
        self.listbox.pack(fill="both", expand=True, padx=8, pady=8)
        self.listbox.bind("<<ListboxSelect>>", self.show_detail)

        # ───────── 右侧：正文区域 ─────────
        right = tk.Frame(self, bg=theme["bg"])
        right.pack(side="right", fill="both", expand=True)

        self.text = tk.Text(
            right,
            bg=theme["bg"],
            fg=theme["fg"],
            wrap="word",
            relief="flat",
        )
        self.text.pack(fill="both", expand=True, padx=12, pady=12)

        self.text.tag_config("title", font=("Segoe UI", 14, "bold"))

    # =================================================
    # 列表加载（由 QueryPanel 调用）
    # =================================================
    def load(self, rows):
        self.data = rows or []
        self.listbox.delete(0, tk.END)

        for r in self.data:
            self.listbox.insert(tk.END, r[0])

        # 自动选中第一条（体验更好）
        if self.data:
            self.listbox.selection_set(0)
            self.show_detail(None)

    # =================================================
    # 点击新闻（UI 线程）
    # =================================================
    def show_detail(self, _):
        if not self.listbox.curselection():
            return

        idx = self.listbox.curselection()[0]
        title, source, region, published, link = self.data[idx]

        # 1️⃣ 先从数据库拿文章
        article = get_article_by_link(link)
        if not article:
            return

        self.current_article = article

        # 2️⃣ 如果没有英文正文，立刻抓并存库
        if not article.get("content_en"):
            content_en = fetch_article_content(link)
            if content_en:
                save_article_en(link, content_en)
                article["content_en"] = content_en
            else:
                article["content_en"] = "[Failed to fetch article content]"

        # 3️⃣ 立即渲染（英文 / 已有内容）
        self.render_current_article()

        # 4️⃣ 🔥 如果需要中文但还没有，后台翻译
        self._maybe_translate_article(article)

    # =================================================
    # UI 线程：根据翻译模式渲染正文（唯一入口）
    # =================================================
    def render_current_article(self):
        if not self.current_article:
            return

        article = self.current_article
        content_en = article.get("content_en", "")
        content_zh = article.get("content_zh", "")

        mode = AppSettings.translate_mode

        if mode == "en_zh":
            text = content_en
            if content_zh:
                text += "\n\n" + content_zh

        elif mode == "zh_only":
            text = content_zh or "[No Chinese translation yet]"

        elif mode == "zh_en":
            text = ""
            if content_zh:
                text += content_zh + "\n\n"
            text += content_en

        else:
            text = content_en

        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, article["title"] + "\n\n", "title")
        self.text.insert(tk.END, text)

    # =================================================
    # 判断是否需要翻译（唯一触发点）
    # =================================================
    def _maybe_translate_article(self, article):
        if not AppSettings.auto_translate:
            return

        if article.get("content_en") and not article.get("content_zh"):
            Thread(
                target=self._translate_and_save_bg,
                args=(article,),
                daemon=True
            ).start()

    # =================================================
    # 后台线程：翻译 + 存库 + 回 UI
    # =================================================
    def _translate_and_save_bg(self, article):
        try:
            zh = translate_en_zh(article["content_en"])

            # 1️⃣ 写数据库
            save_article_zh(article["link"], zh)

            # 2️⃣ 更新内存对象（非常关键）
            article["content_zh"] = zh

            # 3️⃣ 回主线程刷新显示（立即生效）
            self.after(0, self.render_current_article)

        except Exception as e:
            print("Translation failed:", e)
