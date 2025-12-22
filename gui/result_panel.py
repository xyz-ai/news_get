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

        self.data = []                 # [(title, source, region, published, link)]
        self.current_article = None    # dict from DB
        self._translating_link = None
        self._fetching_links = set()

        # ───────── 左侧：新闻列表 ─────────
        self.left = tk.Frame(self, bg=theme["panel"], width=360)
        self.left.pack(side="left", fill="y")
        self.left.pack_propagate(False)

        self.listbox = tk.Listbox(
            self.left,
            bg=theme["panel"],
            fg=theme["fg"],
            selectbackground=theme["accent"],
            highlightthickness=0,
            relief="flat",
        )
        self.listbox.pack(fill="both", expand=True, padx=8, pady=8)
        self.listbox.bind("<<ListboxSelect>>", self.show_detail)

        # ───────── 右侧：正文区域 ─────────
        self.right = tk.Frame(self, bg=theme["bg"])
        self.right.pack(side="right", fill="both", expand=True)

        self.text = tk.Text(
            self.right,
            bg=theme["bg"],
            fg=theme["fg"],
            wrap="word",
            relief="flat",
            padx=14,
            pady=14,
        )
        self.text.pack(fill="both", expand=True, padx=12, pady=12)

        self.text.tag_config("title", font=("Segoe UI", 14, "bold"))
        self.apply_theme()

    # =================================================
    # 主题 / 字体
    # =================================================
    def apply_theme(self):
        theme = get_theme()
        fs = AppSettings.font_size

        self.config(bg=theme["bg"])
        self.left.config(bg=theme["panel"])
        self.right.config(bg=theme["bg"])

        self.listbox.config(
            bg=theme["panel"],
            fg=theme["fg"],
            selectbackground=theme["accent"],
            font=("Segoe UI", fs),
        )

        self.text.config(
            bg=theme["bg"],
            fg=theme["fg"],
            insertbackground=theme["fg"],
            font=("Segoe UI", fs + 1),
            spacing1=4,
            spacing2=2,
            spacing3=8,
        )
        self.text.tag_config("title", font=("Segoe UI", fs + 2, "bold"))

        # 主题刷新后保留当前文章的渲染
        self.render_current_article()

    # =================================================
    # 公共刷新入口
    # =================================================
    def refresh_current(self):
        self.render_current_article()
        self.ensure_translation_for_current_article()

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

        # 2️⃣ 立即渲染（已有内容 or 占位）
        self.render_current_article()

        # 3️⃣ 后台抓取英文正文（避免阻塞 UI）
        self._ensure_content_en(article)

        # 4️⃣ 🔥 按需触发翻译（后台）
        self.ensure_translation_for_current_article()

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
            text = content_en or "[Loading English content...]"
            if content_zh:
                text += "\n\n" + content_zh

        elif mode == "zh_only":
            text = content_zh or "[No Chinese translation yet]"

        elif mode == "zh_en":
            text = ""
            if content_zh:
                text += content_zh + "\n\n"
            text += content_en or "[Loading English content...]"

        else:
            text = content_en or "[Loading English content...]"

        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, article["title"] + "\n\n", "title")
        self.text.insert(tk.END, text)

    # =================================================
    # 统一翻译触发入口
    # =================================================
    def ensure_translation_for_current_article(self):
        """
        判断当前文章是否需要翻译，并在后台触发。
        - 仅在需要中文且开启自动翻译时触发
        - 不重复翻译同一篇文章
        """
        article = self.current_article
        if not article:
            return

        needs_chinese = AppSettings.translate_mode in {"en_zh", "zh_only", "zh_en"}
        if not needs_chinese or not AppSettings.auto_translate:
            return

        if not article.get("content_en"):
            return

        if article.get("content_zh"):
            return

        link = article.get("link")
        if not link or self._translating_link == link:
            return

        self._translating_link = link
        Thread(
            target=self._translate_and_save_bg,
            args=(article,),
            daemon=True,
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
        finally:
            self._translating_link = None

    # =================================================
    # 内容抓取（后台），完成后统一触发翻译检查
    # =================================================
    def _fetch_content_bg(self, article):
        link = article.get("link")
        if not link:
            return
        try:
            content_en = fetch_article_content(link)
            if not content_en:
                content_en = "[Failed to fetch article content]"
            save_article_en(link, content_en)

            def update_article():
                article["content_en"] = content_en
                self.render_current_article()
                self.ensure_translation_for_current_article()

            self.after(0, update_article)
        except Exception as e:
            print("Fetch content failed:", e)
        finally:
            if link in self._fetching_links:
                self._fetching_links.remove(link)

    # =================================================
    # 启动后台抓取英文正文
    # =================================================
    def _ensure_content_en(self, article):
        if article.get("content_en"):
            return

        link = article.get("link")
        if not link or link in self._fetching_links:
            return

        self._fetching_links.add(link)
        Thread(
            target=self._fetch_content_bg,
            args=(article,),
            daemon=True,
        ).start()
