from __future__ import annotations

from typing import Any, Iterable

import flet as ft

from core.article_fetcher import fetch_article_content
from core.article_repo import clear_all_news, get_article_by_link, save_article_en
from core.query_engine import query_news
from core.settings import (
    AppSettings,
    load_settings,
    save_settings,
    set_translate_mode,
    toggle_theme,
)
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

    # ------------------------------------------------------------------ Layout
    def _configure_page(self) -> None:
        self.page.title = "News Desk"
        self.page.padding = 0
        self.page.horizontal_alignment = "stretch"
        self.page.vertical_alignment = "stretch"
        self._apply_theme()

    def _apply_theme(self) -> None:
        palette = self._palette()
        self.page.theme_mode = (
            ft.ThemeMode.DARK if AppSettings.theme == "dark" else ft.ThemeMode.LIGHT
        )
        self.page.bgcolor = palette["bg"]
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=palette["accent"],
                secondary=palette["panel"],
            )
        )

    def _palette(self) -> dict[str, str]:
        return get_theme()

    def _build_ui(self) -> None:
        palette = self._palette()

        self.search_field = ft.TextField(
            value=AppSettings.default_keyword,
            hint_text=t("keyword"),
            dense=True,
            expand=True,
            on_submit=self._on_search,
        )
        self.search_button = ft.FilledButton(
            text=t("search"),
            icon=ft.Icons.SEARCH,
            height=40,
            on_click=self._on_search,
        )

        self.news_list = ft.ListView(
            spacing=8,
            padding=8,
            expand=True,
            auto_scroll=False,
        )

        self.query_label = ft.Text(t("query"), size=13, color=palette["muted"])
        left_column = ft.Column(
            controls=[
                self.query_label,
                ft.Row([self.search_field, self.search_button], spacing=8),
                self.news_list,
            ],
            spacing=10,
            expand=True,
        )
        self.left_panel = ft.Container(
            width=320,
            bgcolor=palette["panel"],
            padding=12,
            border=ft.border.only(right=ft.BorderSide(1, palette["border"])),
            content=left_column,
        )

        self.article_title = ft.Text(
            t("no_article_selected"),
            size=22,
            weight=ft.FontWeight.W_700,
            color=palette["fg"],
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.article_meta = ft.Text("", size=12, color=palette["muted"])
        self.translation_indicator = ft.Text(
            self._translate_mode_label(),
            size=12,
            color=palette["muted"],
        )
        self.article_body = ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.article_status = ft.Text("", size=12, color=palette["muted"])

        article_container = ft.Container(
            bgcolor=palette["panel"],
            padding=16,
            border_radius=12,
            content=self.article_body,
            expand=True,
        )

        article_column = ft.Column(
            controls=[
                self.article_title,
                self.article_meta,
                self.translation_indicator,
                article_container,
                self.article_status,
            ],
            spacing=12,
            expand=True,
        )
        self.right_panel = ft.Container(
            bgcolor=palette["bg"],
            padding=16,
            content=article_column,
            expand=True,
        )

        self.settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS_OUTLINED,
            tooltip=t("settings"),
            on_click=self._open_settings,
        )
        self.title_text = ft.Text(
            "News Desk", size=18, weight=ft.FontWeight.W_700, color=palette["fg"]
        )
        top_row = ft.Row(
            controls=[
                self.title_text,
                ft.Container(expand=True),
                self.settings_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.top_bar = ft.Container(
            bgcolor=palette["panel"],
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border=ft.border.only(bottom=ft.BorderSide(1, palette["border"])),
            content=top_row,
        )

        body_row = ft.Row(
            controls=[self.left_panel, self.right_panel],
            spacing=0,
            expand=True,
        )
        self.root = ft.Column(
            controls=[self.top_bar, body_row],
            spacing=0,
            expand=True,
        )

        self._refresh_colors()
        self._render_article_content()

    # ------------------------------------------------------------------ Actions
    def _perform_initial_search(self) -> None:
        initial_keyword = AppSettings.default_keyword or ""
        self.search_news(initial_keyword)

    def _on_search(self, _) -> None:
        keyword = (self.search_field.value or "").strip()
        self.search_news(keyword)

    def search_news(self, keyword: str) -> None:
        self.article_status.value = ""
        self.page.update()
        try:
            rows = query_news(keyword=keyword or None)
            self.news_rows = rows or []
        except Exception as exc:  # pragma: no cover - runtime guardrail
            self.news_rows = []
            self._populate_news_list()
            self._clear_article_view(message=f"Search failed: {exc}")
            self.page.update()
            return

        self._populate_news_list()
        if self.news_rows:
            self.select_article(self.news_rows[0])
        else:
            self._clear_article_view(message=t("no_article_selected"))
        self.page.update()

    def _populate_news_list(self) -> None:
        palette = self._palette()
        self.news_list.controls.clear()
        for row in self.news_rows:
            title, source, region, published, link = row
            tile = ft.Container(
                data=link,
                bgcolor=self._tile_bgcolor(link),
                padding=10,
                border_radius=8,
                ink=True,
                on_click=lambda _, r=row: self.select_article(r),
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(
                            title,
                            weight=ft.FontWeight.W_600,
                            size=14,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            color=palette["fg"],
                        ),
                        ft.Text(
                            f"{source} · {region} · {published}",
                            size=11,
                            color=palette["muted"],
                        ),
                    ],
                ),
            )
            self.news_list.controls.append(tile)
        self.news_list.update()
        self._update_selection_highlight()

    def select_article(self, row: Iterable) -> None:
        title, source, region, published, link = row
        self.selected_link = link
        self._update_selection_highlight()

        article = get_article_by_link(link)
        if not article:
            article = {"title": title, "link": link, "content_en": None, "content_zh": None}
        self.current_article = article

        self.article_title.value = article.get("title") or title
        self.article_meta.value = f"{source} · {region} · {published}"
        self.translation_indicator.value = self._translate_mode_label()

        if not article.get("content_en"):
            self.article_status.value = t("loading_article")
            self._render_article_content(placeholder=t("loading_article"))
            self.page.update()
            content = fetch_article_content(link)
            save_article_en(link, content)
            article["content_en"] = content
            self.article_status.value = ""

        self._render_article_content()
        self.page.update()

    def _clear_article_view(self, message: str) -> None:
        palette = self._palette()
        self.current_article = None
        self.article_title.value = t("no_article_selected")
        self.article_meta.value = ""
        self.translation_indicator.value = self._translate_mode_label()
        self.article_body.controls.clear()
        self.article_body.controls.append(
            ft.Text(message, color=palette["muted"])
        )
        self.article_status.value = message

    def _render_article_content(self, placeholder: str | None = None) -> None:
        palette = self._palette()
        self.article_body.controls.clear()

        if placeholder:
            self.article_body.controls.append(ft.Text(placeholder, color=palette["muted"]))
            return

        if not self.current_article:
            self.article_body.controls.append(
                ft.Text(t("no_article_selected"), color=palette["muted"])
            )
            return

        article = self.current_article
        content_en = (article.get("content_en") or "").strip()
        content_zh = (article.get("content_zh") or "").strip()

        sections: list[tuple[str, str]] = []
        mode = AppSettings.translate_mode

        if mode == "zh_only":
            sections.append(("中文", content_zh or t("no_translation_yet")))
        elif mode == "zh_en":
            sections.append(("中文", content_zh or t("no_translation_yet")))
            sections.append(("English", content_en or t("loading_article")))
        elif mode == "en_zh":
            sections.append(("English", content_en or t("loading_article")))
            sections.append(("中文", content_zh or t("no_translation_yet")))
        else:
            sections.append(("English", content_en or t("loading_article")))

        for idx, (label, body) in enumerate(sections):
            self.article_body.controls.append(
                ft.Text(label, weight=ft.FontWeight.W_600, color=palette["muted"])
            )
            self.article_body.controls.append(
                ft.Text(body, selectable=True, color=palette["fg"], size=15)
            )
            if idx < len(sections) - 1:
                self.article_body.controls.append(
                    ft.Divider(height=1, color=palette["border"])
                )

    def _update_selection_highlight(self) -> None:
        palette = self._palette()
        for tile in self.news_list.controls:
            link = getattr(tile, "data", None)
            tile.bgcolor = self._tile_bgcolor(link)
            if isinstance(tile.content, ft.Column) and tile.content.controls:
                for idx, child in enumerate(tile.content.controls):
                    if isinstance(child, ft.Text):
                        child.color = palette["fg"] if idx == 0 else palette["muted"]
        self.news_list.update()

    def _tile_bgcolor(self, link: str | None) -> str:
        palette = self._palette()
        if self.selected_link and link == self.selected_link:
            return palette["button"]
        return palette["panel"]

    # ------------------------------------------------------------------ Settings
    def _open_settings(self, _) -> None:
        palette = self._palette()

        theme_switch = ft.Switch(
            label=t("toggle_theme"),
            value=AppSettings.theme == "dark",
            on_change=self._handle_theme_toggle,
        )
        translate_modes = ft.RadioGroup(
            value=AppSettings.translate_mode if AppSettings.translate_mode in {"en_zh", "zh_only", "zh_en"} else "en_only",
            on_change=self._handle_translate_mode_change,
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Radio(value="en_zh", label=t("mode_en_zh")),
                    ft.Radio(value="zh_only", label=t("mode_zh_only")),
                    ft.Radio(value="zh_en", label=t("mode_zh_en")),
                    ft.Radio(value="en_only", label=t("mode_en_only")),
                ],
            ),
        )
        clear_button = ft.OutlinedButton(
            text=t("clear_all_data"),
            icon=ft.Icons.DELETE_SWEEP,
            on_click=self._handle_clear_database,
        )

        dialog_content = ft.Column(
            spacing=14,
            width=440,
            controls=[
                ft.Text(t("settings_title"), size=18, weight=ft.FontWeight.W_700),
                ft.Text(t("appearance"), weight=ft.FontWeight.W_600, color=palette["muted"]),
                theme_switch,
                ft.Text(t("translation"), weight=ft.FontWeight.W_600, color=palette["muted"]),
                translate_modes,
                clear_button,
            ],
        )

        self.settings_dialog = ft.AlertDialog(
            modal=True,
            content=dialog_content,
            actions=[
                ft.TextButton(text=t("save"), icon=ft.Icons.CHECK, on_click=self._close_settings)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = self.settings_dialog
        self.settings_dialog.open = True
        self.page.update()

    def _close_settings(self, _) -> None:
        if self.settings_dialog:
            self.settings_dialog.open = False
            self.page.update()

    def _handle_theme_toggle(self, _) -> None:
        toggle_theme()
        self._apply_theme()
        self._refresh_colors()
        self._render_article_content()
        self._populate_news_list()
        self.page.update()

    def _handle_translate_mode_change(self, e: ft.ControlEvent) -> None:
        value = e.control.value
        if value in {"en_zh", "zh_only", "zh_en"}:
            set_translate_mode(value)
        else:
            AppSettings.translate_mode = "en_only"
            save_settings()
        self.translation_indicator.value = self._translate_mode_label()
        self._render_article_content()
        self.page.update()

    def _handle_clear_database(self, _) -> None:
        clear_all_news()
        self.news_rows.clear()
        self.news_list.controls.clear()
        self.selected_link = None
        self._clear_article_view(message=t("clear_all_data"))
        self.page.update()

    def _refresh_colors(self) -> None:
        palette = self._palette()
        self.page.bgcolor = palette["bg"]
        self.top_bar.bgcolor = palette["panel"]
        self.top_bar.border = ft.border.only(bottom=ft.BorderSide(1, palette["border"]))
        self.left_panel.bgcolor = palette["panel"]
        self.left_panel.border = ft.border.only(right=ft.BorderSide(1, palette["border"]))
        self.right_panel.bgcolor = palette["bg"]

        self.title_text.color = palette["fg"]
        self.query_label.color = palette["muted"]
        self.search_field.fill_color = palette["bg"]
        self.search_field.border_color = palette["border"]
        self.search_field.color = palette["fg"]
        self.article_title.color = palette["fg"]
        self.article_meta.color = palette["muted"]
        self.translation_indicator.color = palette["muted"]
        self.article_status.color = palette["muted"]

    # ------------------------------------------------------------------ Helpers
    def _translate_mode_label(self) -> str:
        label_map = {
            "en_zh": t("mode_en_zh"),
            "zh_only": t("mode_zh_only"),
            "zh_en": t("mode_zh_en"),
        }
        return f"{t('translation')}: {label_map.get(AppSettings.translate_mode, t('mode_en_only'))}"


def main(page: ft.Page):
    NewsDeskApp(page)


if __name__ == "__main__":
    ft.app(target=main)
