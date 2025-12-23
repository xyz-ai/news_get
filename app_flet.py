from __future__ import annotations

import asyncio
from typing import Any, Callable, Iterable

import flet as ft

from flet.controls import page

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


def _run_in_executor(func: Callable[[], Any]) -> asyncio.Future:
    # ✅ 必须在 async 上下文中使用 get_running_loop()
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, func)


class NewsDeskApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "News Desk"
        self.page.padding = 0
        self.page.horizontal_alignment = "stretch"
        self.page.vertical_alignment = "stretch"
        self.page.scroll = "adaptive"
        self._apply_theme()

        self.news_rows: list[tuple] = []
        self.current_article: dict[str, Any] | None = None
        self.selected_link: str | None = None
        self._fetching_links: set[str] = set()
        self._translating_link: str | None = None
        self._settings_dialog: ft.AlertDialog | None = None

        # ✅ 事件处理函数直接做 async（不要 page.run_task + lambda）
        self.search_field = ft.TextField(
            value=AppSettings.default_keyword,
            hint_text=t("keyword"),
            prefix_icon=ft.Icons.SEARCH,
            border_radius=8,
            dense=True,
            filled=True,
            on_submit=self._on_search_submit_async,   # ✅ async handler
            expand=True,
        )
        self.search_button = ft.FilledButton(
            text=t("search"),
            icon=ft.Icons.SEARCH,
            on_click=self._on_search_click_async,     # ✅ async handler
            height=44,
        )
        self.settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS_OUTLINED,
            tooltip=t("settings"),
            on_click=self._open_settings,             # sync ok（只是打开弹窗）
        )

        self.news_list = ft.ListView(
            spacing=8,
            padding=12,
            expand=True,
            auto_scroll=False,
        )

        self.article_title = ft.Text(
            value=t("no_article_selected"),
            weight=ft.FontWeight.W_700,
            size=20,
            color=get_theme()["fg"],
        )
        self.article_meta = ft.Text(value="", color=get_theme().get("muted", "#888888"))
        self.article_body = ft.Markdown(
            value="",
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        )

        # ✅ 滚动要加在 Column/ListView 上，不是 Markdown/Container
        self.article_body_scroller = ft.Column(
            controls=[self.article_body],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        self.article_body_container = ft.Container(
            content=self.article_body_scroller,
            expand=True,
        )

        self.article_status = ft.Text(
            value="",
            color=get_theme().get("muted", "#888888"),
            size=12,
        )

        self.layout = ft.Column(
            spacing=0,
            controls=[
                self._build_top_bar(),
                self._build_body(),
            ],
            expand=True,
        )

        self.page.add(self.layout)
        self.page.update()

        # ✅ 这里可以用 run_task：传协程函数（不是调用结果）
        self.page.run_task(self._initial_search)

    # ------------------------------------------------------------------ UI
    def _palette(self):
        theme = get_theme()
        return {
            "bg": theme["bg"],
            "panel": theme["panel"],
            "panel_alt": theme.get("button", theme["panel"]),
            "fg": theme["fg"],
            "muted": theme.get("muted", "#888888"),
            "accent": theme["accent"],
            "border": theme["border"],
        }

    def _apply_theme(self):
        self.page.theme_mode = (
            ft.ThemeMode.DARK if AppSettings.theme == "dark" else ft.ThemeMode.LIGHT
        )
        palette = get_theme()
        self.page.bgcolor = palette["bg"]
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=palette["accent"],
                secondary=palette["panel"],
            ),
            font_family="Segoe UI",
        )

    def _build_top_bar(self) -> ft.Container:
        palette = self._palette()
        self.search_field.fill_color = palette["bg"]
        self.search_field.border_color = palette["border"]
        self.search_field.cursor_color = palette["fg"]
        self.search_field.color = palette["fg"]

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=palette["panel"],
            content=ft.Row(
                controls=[
                    ft.Text(
                        t("title"),
                        weight=ft.FontWeight.W_700,
                        size=18,
                        color=palette["fg"],
                    ),
                    self.search_field,
                    self.search_button,
                    self.settings_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _build_body(self) -> ft.Container:
        palette = self._palette()
        left_panel = ft.Container(
            width=340,
            bgcolor=palette["panel"],
            border=ft.border.only(right=ft.BorderSide(1, palette["border"])),
            content=ft.Column(
                controls=[
                    ft.Text(
                        t("query"),
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=palette["muted"],
                    ),
                    self.news_list,
                ],
                spacing=10,
                expand=True,
            ),
        )

        article_area = ft.Container(
            bgcolor=palette["bg"],
            padding=ft.padding.only(left=18, right=18, top=12, bottom=18),
            expand=True,
            content=ft.Column(
                controls=[
                    self.article_title,
                    self.article_meta,
                    ft.Container(height=8),
                    ft.Container(
                        content=self.article_body_container,
                        bgcolor=palette["panel"],
                        border_radius=12,
                        padding=0,
                        expand=True,
                    ),
                    self.article_status,
                ],
                spacing=10,
                expand=True,
            ),
        )

        return ft.Container(
            expand=True,
            bgcolor=palette["bg"],
            content=ft.Row(
                controls=[left_panel, article_area],
                spacing=0,
                expand=True,
            ),
        )

    # ------------------------------------------------------------------ Actions
    async def _initial_search(self):
        await self._search(keyword=AppSettings.default_keyword)

    async def _on_search_submit_async(self, e):
        await self._search(self.search_field.value.strip())

    async def _on_search_click_async(self, e):
        await self._search(self.search_field.value.strip())

    async def _search(self, keyword: str | None):
        self.search_button.disabled = True
        self.search_button.icon = ft.Icons.HOURGLASS_BOTTOM
        self.article_status.value = ""
        self.page.update()

        cleaned_kw = (keyword or "").strip()
        try:
            rows = await _run_in_executor(lambda: query_news(keyword=cleaned_kw or None))
            self.news_rows = rows or []
            self._render_news_list(select_first=True)
        except Exception as e:
            self.article_status.value = f"Search failed: {e}"
            self.page.update()
        finally:
            self.search_button.disabled = False
            self.search_button.icon = ft.Icons.SEARCH
            self.page.update()

    def _render_news_list(self, select_first: bool = False):
        palette = self._palette()
        self.news_list.controls.clear()

        for row in self.news_rows:
            title, source, region, published, link = row

            async def _click(e, r=row):
                await self._handle_select(r)

            tile = ft.Container(
                data=link,
                bgcolor=palette["panel"],
                border_radius=10,
                padding=12,
                ink=True,
                on_click=_click,  # ✅ 直接 async handler
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(
                            title,
                            weight=ft.FontWeight.W_600,
                            color=palette["fg"],
                            size=14,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(
                            f"{source} · {region} · {published}",
                            color=palette["muted"],
                            size=12,
                        ),
                    ],
                ),
            )
            self.news_list.controls.append(tile)

        self._update_list_highlight()

        if select_first and self.news_rows:
            # ✅ 这里也别用 run_task；直接 schedule
            async def _select_first():
                await self._handle_select(self.news_rows[0])

            asyncio.create_task(_select_first())

        self.news_list.update()

    def _update_list_highlight(self):
        palette = self._palette()
        for tile in self.news_list.controls:
            link = tile.data
            tile.bgcolor = palette["panel_alt"] if link == self.selected_link else palette["panel"]
            if isinstance(tile.content, ft.Column):
                for idx, child in enumerate(tile.content.controls):
                    if isinstance(child, ft.Text):
                        child.color = palette["fg"] if idx == 0 else palette["muted"]
        self.news_list.update()

    async def _handle_select(self, row: Iterable):
        title, source, region, published, link = row
        self.selected_link = link
        self._update_list_highlight()

        article = await _run_in_executor(lambda: get_article_by_link(link))
        if not article:
            self.article_title.value = title
            self.article_meta.value = f"{source} · {region} · {published}"
            self.article_body.value = t("loading_article")
            self.article_status.value = t("loading_article")
            self.page.update()
            return

        self.current_article = article
        self.article_meta.value = f"{source} · {region} · {published}"
        self.article_title.value = article.get("title") or title
        self._render_article()
        self.page.update()

        # ✅ 没英文正文则抓取
        if not article.get("content_en") and link not in self._fetching_links:
            self._fetching_links.add(link)
            asyncio.create_task(self._fetch_content(article))

        # ✅ 需要时翻译
        self._ensure_translation(article)

    def _render_article(self):
        if not self.current_article:
            self.article_title.value = t("no_article_selected")
            self.article_body.value = ""
            self.article_status.value = ""
            return

        article = self.current_article
        content_en = (article.get("content_en") or "").strip()
        content_zh = (article.get("content_zh") or "").strip()
        mode = AppSettings.translate_mode

        sections: list[str] = []
        if mode == "en_zh":
            sections.append(content_en or t("loading_article"))
            if content_zh:
                sections.append(content_zh)
        elif mode == "zh_only":
            sections.append(content_zh or t("no_translation_yet"))
        elif mode == "zh_en":
            sections.append(content_zh or t("no_translation_yet"))
            sections.append(content_en or t("loading_article"))
        else:
            sections.append(content_en or t("loading_article"))

        self.article_body.value = "\n\n".join(sections)
        self.article_body.code_theme = (
            "atom-one-dark" if AppSettings.theme == "dark" else "atom-one-light"
        )

        self.article_status.value = (
            t("translation")
            + ": "
            + {
                "en_only": t("mode_en_only"),
                "en_zh": t("mode_en_zh"),
                "zh_only": t("mode_zh_only"),
                "zh_en": t("mode_zh_en"),
            }.get(mode, t("mode_en_only"))
        )

        self.page.update()

    async def _fetch_content(self, article: dict[str, Any]):
        link = article.get("link")
        if not link:
            return
        try:
            content_en = await _run_in_executor(lambda: fetch_article_content(link))
            if not content_en:
                content_en = "[Failed to fetch article content]"
            await _run_in_executor(lambda: save_article_en(link, content_en))
            article["content_en"] = content_en
            self._render_article()
            self._ensure_translation(article)
        finally:
            self._fetching_links.discard(link)
            self.page.update()

    def _ensure_translation(self, article: dict[str, Any]):
        mode = AppSettings.translate_mode
        needs_chinese = mode in {"en_zh", "zh_only", "zh_en"}
        if not needs_chinese or not AppSettings.auto_translate:
            return
        if article.get("content_zh"):
            return
        if not article.get("content_en"):
            return

        link = article.get("link")
        if not link or self._translating_link == link:
            return

        self._translating_link = link
        asyncio.create_task(self._translate_article(article))

    async def _translate_article(self, article: dict[str, Any]):
        link = article.get("link")
        try:
            zh_result = await _run_in_executor(
                lambda: translate_en_zh(article.get("content_en", ""), link=link)
            )
            content_to_save = zh_result.text
            if zh_result.note:
                content_to_save = f"[Partial translation] {zh_result.note}\n\n{zh_result.text}"

            if content_to_save and content_to_save.strip():
                if zh_result.translation_status == "success":
                    await _run_in_executor(lambda: save_article_zh(link, content_to_save))
                article["content_zh"] = content_to_save
                self._render_article()
        except TranslationError as e:
            msg = str(e)
            article["content_zh"] = msg
            await _run_in_executor(lambda: save_article_zh(link, msg))
            self._render_article()
        except Exception as e:
            article["content_zh"] = f"[Translation failed] {e}"
            self._render_article()
        finally:
            self._translating_link = None
            self.page.update()

    # ------------------------------------------------------------------ Settings
    def _open_settings(self, e):
        palette = self._palette()
        translate_modes = [
            ("en_only", t("mode_en_only")),
            ("en_zh", t("mode_en_zh")),
            ("zh_only", t("mode_zh_only")),
            ("zh_en", t("mode_zh_en")),
        ]

        theme_switch = ft.Switch(
            label=t("toggle_theme"),
            value=AppSettings.theme == "dark",
            on_change=self._toggle_theme,
        )
        language_dropdown = ft.Dropdown(
            label=t("language"),
            options=[
                ft.dropdown.Option("en", "English"),
                ft.dropdown.Option("zh", "中文"),
            ],
            value=AppSettings.language,
            on_change=self._change_language,
        )
        mode_selector = ft.RadioGroup(
            value=AppSettings.translate_mode if AppSettings.translate_mode in {"en_zh", "zh_only", "zh_en"} else "en_only",
            content=ft.Column(controls=[ft.Radio(value=k, label=lb) for k, lb in translate_modes]),
            on_change=self._change_translate_mode,
        )
        auto_translate_switch = ft.Switch(
            label=t("auto_translate"),
            value=getattr(AppSettings, "auto_translate", True),
            on_change=self._toggle_auto_translate,
        )

        def update_days(e2: ft.ControlEvent):
            try:
                AppSettings.default_days = int(e2.control.value or AppSettings.default_days)
            except ValueError:
                e2.control.value = str(AppSettings.default_days)
                e2.control.update()

        defaults_fields = ft.Column(
            spacing=10,
            controls=[
                ft.TextField(
                    label=t("keyword"),
                    value=AppSettings.default_keyword,
                    on_change=lambda ev: setattr(AppSettings, "default_keyword", ev.control.value),
                ),
                ft.TextField(
                    label=t("days"),
                    value=str(AppSettings.default_days),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    on_change=update_days,
                ),
                ft.Dropdown(
                    label=t("source"),
                    options=[
                        ft.dropdown.Option("ALL"),
                        ft.dropdown.Option("BBC"),
                        ft.dropdown.Option("Guardian"),
                        ft.dropdown.Option("Fox"),
                    ],
                    value=AppSettings.default_source,
                    on_change=lambda ev: setattr(AppSettings, "default_source", ev.control.value),
                ),
            ],
        )

        async def _fetch_latest_click(ev):
            await self._fetch_latest()

        async def _clear_all_click(ev):
            await self._clear_all_data()

        action_buttons = ft.Row(
            controls=[
                ft.FilledButton(
                    text=t("fetch_latest"),
                    icon=ft.Icons.UPDATE,
                    on_click=_fetch_latest_click,   # ✅ async
                ),
                ft.OutlinedButton(
                    text=t("clear_all_data"),
                    icon=ft.Icons.DELETE_SWEEP,
                    on_click=_clear_all_click,      # ✅ async
                ),
            ],
            spacing=12,
        )

        content = ft.Column(
            spacing=18,
            controls=[
                ft.Text(t("settings_title"), size=18, weight=ft.FontWeight.W_700),
                ft.Text(t("appearance"), weight=ft.FontWeight.W_600, color=palette["muted"]),
                theme_switch,
                language_dropdown,
                ft.Text(t("translation"), weight=ft.FontWeight.W_600, color=palette["muted"]),
                mode_selector,
                auto_translate_switch,
                ft.Text(t("auto_translate_note"), size=12, color=palette["muted"]),
                ft.Text(t("default_params"), weight=ft.FontWeight.W_600, color=palette["muted"]),
                defaults_fields,
                action_buttons,
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.TextButton(
                            text=t("save"),
                            icon=ft.Icons.SAVE_OUTLINED,
                            on_click=lambda _: self._save_settings(),
                        )
                    ],
                ),
            ],
            width=520,
            scroll=ft.ScrollMode.AUTO,
        )

        self._settings_dialog = ft.AlertDialog(
            modal=True,
            content=content,
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = self._settings_dialog
        self._settings_dialog.open = True
        self.page.update()

    def _save_settings(self):
        save_settings()
        if self._settings_dialog:
            self._settings_dialog.open = False
        self._apply_theme()
        self._rebuild_shell()

    def _toggle_theme(self, e: ft.ControlEvent):
        toggle_theme()
        self._apply_theme()
        self._rebuild_shell()

    def _change_language(self, e: ft.ControlEvent):
        AppSettings.language = e.control.value
        save_settings()
        self._refresh_labels()

    def _change_translate_mode(self, e: ft.ControlEvent):
        value = e.control.value
        if value in {"en_zh", "zh_only", "zh_en"}:
            set_translate_mode(value)
        else:
            AppSettings.translate_mode = "en_only"
            save_settings()
        self._render_article()
        if self.current_article:
            self._ensure_translation(self.current_article)
        self.page.update()

    def _toggle_auto_translate(self, e: ft.ControlEvent):
        AppSettings.auto_translate = bool(e.control.value)
        save_settings()
        if self.current_article:
            self._ensure_translation(self.current_article)

    def _refresh_labels(self):
        self.search_field.hint_text = t("keyword")
        self.search_button.text = t("search")
        self.article_status.value = ""
        self._rebuild_shell()

    # ------------------------------------------------------------------ Data actions
    async def _fetch_latest(self):
        progress = ft.SnackBar(ft.Text(t("fetch_latest") + "..."), open=True)
        self.page.snack_bar = progress
        self.page.update()
        try:
            await _run_in_executor(self._run_fetch_latest)
            await self._search(self.search_field.value.strip())
        finally:
            progress.open = False
            self.page.update()

    def _run_fetch_latest(self):
        from news_fetch_and_store import fetch_and_store, init_db
        init_db()
        fetch_and_store()

    async def _clear_all_data(self):
        await _run_in_executor(clear_all_news)
        self.news_rows.clear()
        self.current_article = None
        self.selected_link = None
        self._fetching_links.clear()
        self._translating_link = None
        self.news_list.controls.clear()
        self.article_title.value = t("title")
        self.article_meta.value = ""
        self.article_body.value = ""
        self.article_status.value = ""
        self.page.update()

    def _rebuild_shell(self):
        self.layout.controls[0] = self._build_top_bar()
        self.layout.controls[1] = self._build_body()
        self.page.controls.clear()
        self.page.add(self.layout)
        self._update_list_highlight()
        self._render_article()
        self.page.update()

# ================== APP ENTRY ==================

def main(page: ft.Page):
    NewsDeskApp(page)


if __name__ == "__main__":
    ft.run(main)

