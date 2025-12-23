from __future__ import annotations
from typing import Any, Iterable

import flet as ft
import threading
from news_fetch_and_store import fetch_and_store, init_db

from core.article_fetcher import fetch_article_content
from core.article_repo import (
    clear_all_news,
    get_article_by_link,
    save_article_en,
    save_article_zh,
)
from core.query_engine import query_news
from core.settings import (
    AppSettings,
    load_settings,
    save_settings,
    set_translate_mode,
    toggle_theme,
)
from core.translator import TranslationError, translate_en_zh
from gui.i18n import t
from gui.theme import get_theme


load_settings()


class NewsDeskApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.news_rows: list[tuple] = []
        self.current_article: dict[str, Any] | None = None
        self.selected_link: str | None = None

        self.settings_dialog: ft.AlertDialog | None = None

        self._configure_page()
        self._build_ui()
        self.page.add(self.root)
        self.page.update()

        self._perform_initial_search()

    def _fetch_latest_news(self):
        def task():
            try:
                init_db()
                fetch_and_store()
                self.article_status.value = "News updated."
                # ⭐ 抓取完成后，重新查询当前关键词
                keyword = (self.search_field.value or "").strip()
                self.news_rows = query_news(keyword=keyword or None) or []
                self._populate_news_list()

                if self.news_rows:
                    self.select_article(self.news_rows[0])
                else:
                    self._clear_article_view("No news found.")

                self.article_status.value = "✅ News updated."
            except Exception as e:
                self.article_status.value = f"❌ Fetch failed: {e}"
            finally:
                self.page.update()

        self.article_status.value = "⏳ Fetching latest news..."
        self.page.update()

        threading.Thread(target=task, daemon=True).start()



    # ──────────────────────────────
    # Page / Theme
    # ──────────────────────────────
    def _configure_page(self):
        self.page.title = "News Desk"
        self.page.padding = 0
        self.page.horizontal_alignment = "stretch"
        self.page.vertical_alignment = "stretch"
        self._apply_theme()

    def _palette(self):
        return get_theme()

    def _apply_theme(self):
        palette = self._palette()
        self.page.theme_mode = (
            ft.ThemeMode.DARK if AppSettings.theme == "dark" else ft.ThemeMode.LIGHT
        )
        self.page.bgcolor = palette["bg"]

    # ──────────────────────────────
    # UI
    # ──────────────────────────────
    def _build_ui(self):
        palette = self._palette()

        self.search_field = ft.TextField(
            value=AppSettings.default_keyword,
            hint_text=t("keyword"),
            expand=True,
            on_submit=self._on_search,
        )

        self.search_button = ft.FilledButton(
            text=t("search"),
            icon=ft.Icons.SEARCH,
            on_click=self._on_search,
        )

        self.news_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=8,
        )

        self.left_panel = ft.Container(
            width=320,
            bgcolor=palette["panel"],
            padding=12,
            border=ft.border.only(right=ft.BorderSide(1, palette["border"])),
            content=ft.Column(
                expand=True,
                spacing=10,
                controls=[
                    ft.Text(t("query"), size=13, color=palette["muted"]),
                    ft.Row([self.search_field, self.search_button], spacing=8),
                    self.news_list,
                ],
            ),
        )

        self.article_title = ft.Text(
            t("no_article_selected"),
            size=22,
            weight=ft.FontWeight.BOLD,
        )

        self.article_meta = ft.Text(size=12, color=palette["muted"])
        self.translation_indicator = ft.Text(size=12, color=palette["muted"])

        self.article_body = ft.Column(
            expand=True,
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        )

        self.article_status = ft.Text(size=12, color=palette["muted"])

        self.right_panel = ft.Container(
            expand=True,
            padding=16,
            content=ft.Column(
                expand=True,
                spacing=12,
                controls=[
                    self.article_title,
                    self.article_meta,
                    self.translation_indicator,
                    ft.Container(
                        expand=True,
                        padding=16,
                        bgcolor=palette["panel"],
                        border_radius=10,
                        content=self.article_body,
                    ),
                    self.article_status,
                ],
            ),
        )

        self.settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS_OUTLINED,
            tooltip=t("settings"),
            on_click=self._open_settings,
        )

        self.top_bar = ft.Container(
            bgcolor=palette["panel"],
            padding=12,
            border=ft.border.only(bottom=ft.BorderSide(1, palette["border"])),
            content=ft.Row(
                controls=[
                    ft.Text("News Desk", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    self.settings_button,
                ]
            ),
        )

        self.root = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                self.top_bar,
                ft.Row(expand=True, controls=[self.left_panel, self.right_panel]),
            ],
        )

    # ──────────────────────────────
    # Actions
    # ──────────────────────────────
    def _perform_initial_search(self):
        self.search_news(AppSettings.default_keyword or "")

    def _on_search(self, e):
        self.search_news((self.search_field.value or "").strip())

    def search_news(self, keyword: str):
        self.news_rows = query_news(keyword=keyword or None) or []
        self._populate_news_list()

        if self.news_rows:
            self.select_article(self.news_rows[0])
        else:
            self._clear_article_view(t("no_article_selected"))

        self.page.update()

    def _populate_news_list(self):
        palette = self._palette()
        self.news_list.controls.clear()

        for row in self.news_rows:
            title, source, region, published, link = row
            self.news_list.controls.append(
                ft.Container(
                    data=link,
                    padding=10,
                    border_radius=8,
                    bgcolor=palette["panel"],
                    ink=True,
                    on_click=lambda e, r=row: self.select_article(r),
                    content=ft.Column(
                        controls=[
                            ft.Text(title, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(
                                f"{source} · {region} · {published}",
                                size=11,
                                color=palette["muted"],
                            ),
                        ]
                    ),
                )
            )

    def select_article(self, row: Iterable):
        title, source, region, published, link = row
        self.selected_link = link

        article = get_article_by_link(link) or {
            "title": title,
            "link": link,
            "content_en": None,
            "content_zh": None,
        }
        self.current_article = article

        self.article_title.value = article.get("title", title)
        self.article_meta.value = f"{source} · {region} · {published}"
        self.translation_indicator.value = self._translate_mode_label()

        if not article.get("content_en"):
            content = fetch_article_content(link)
            save_article_en(link, content)
            article["content_en"] = content

        self._ensure_translation(article)
        self._render_article()
        self.page.update()

    # ──────────────────────────────
    # Article render
    # ──────────────────────────────
    def _render_article(self):
        self.article_body.controls.clear()

        article = self.current_article
        if not article:
            return

        mode = AppSettings.translate_mode
        en = article.get("content_en", "")
        zh = article.get("content_zh", "")

        if mode in ("en_zh", "zh_en"):
            self.article_body.controls += [
                ft.Text("English", weight=ft.FontWeight.BOLD),
                ft.Text(en, selectable=True),
                ft.Divider(),
                ft.Text("中文", weight=ft.FontWeight.BOLD),
                ft.Text(zh or t("no_translation_yet"), selectable=True),
            ]
        elif mode == "zh_only":
            self.article_body.controls.append(ft.Text(zh or t("no_translation_yet"), selectable=True))
        else:
            self.article_body.controls.append(ft.Text(en, selectable=True))

    def _clear_article_view(self, msg: str):
        self.article_body.controls.clear()
        self.article_body.controls.append(ft.Text(msg))

    # ──────────────────────────────
    # Settings dialog (0.28.3 正确方式)
    # ──────────────────────────────
    def _open_settings(self, e):
        if self.settings_dialog:
            self.settings_dialog.open = True
            self.page.update()
            return

        theme_switch = ft.Switch(
            label=t("toggle_theme"),
            value=AppSettings.theme == "dark",
            on_change=lambda e: self._handle_theme_toggle(),
        )

        clear_btn = ft.OutlinedButton(
            text=t("clear_all_data"),
            icon=ft.Icons.DELETE_OUTLINE,
            on_click=self._handle_clear_database,
        )

        fetch_btn = ft.FilledButton(
            text="Fetch latest news",
            icon=ft.Icons.DOWNLOAD,
            on_click=lambda e: self._fetch_latest_news(),
        )

        self.settings_dialog = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                width=420,
                spacing=12,
                controls=[
                    ft.Text(t("settings_title"), size=18, weight=ft.FontWeight.BOLD),
                    theme_switch,
                    fetch_btn,
                    clear_btn,
                ],
            ),
            actions=[
                ft.TextButton(
                    text=t("save"),
                    icon=ft.Icons.CHECK,
                    on_click=self._close_settings,
                )
            ],
        )

        self.page.overlay.append(self.settings_dialog)
        self.settings_dialog.open = True
        self.page.update()

    def _close_settings(self, e):
        if self.settings_dialog:
            self.settings_dialog.open = False
            self.page.update()

    # ──────────────────────────────
    # Helpers
    # ──────────────────────────────
    def _handle_theme_toggle(self):
        toggle_theme()
        self._apply_theme()
        self.page.update()

    def _handle_clear_database(self, e):
        clear_all_news()
        self.news_list.controls.clear()
        self._clear_article_view(t("clear_all_data"))
        self.page.update()

    def _ensure_translation(self, article):
        if AppSettings.translate_mode not in {"en_zh", "zh_only", "zh_en"}:
            return
        if article.get("content_zh"):
            return

        try:
            result = translate_en_zh(article["content_en"], link=article["link"])
            save_article_zh(article["link"], result.text)
            article["content_zh"] = result.text
        except Exception as exc:
            article["content_zh"] = str(exc)

    def _translate_mode_label(self):
        return f"{t('translation')}: {AppSettings.translate_mode}"


def main(page: ft.Page):
    NewsDeskApp(page)


if __name__ == "__main__":
    ft.app(target=main)
