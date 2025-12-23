from __future__ import annotations

import asyncio
from typing import Any, Callable, Iterable

import flet as ft

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
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, func)


class NewsDeskApp:
    """
    Modern Flet shell that layers on top of the existing core logic.
    All network / DB work is pushed into the executor to keep the UI responsive.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "News Desk"
        self.page.padding = 0
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.horizontal_alignment = "stretch"
        self.page.vertical_alignment = "stretch"

        self.news_rows: list[tuple] = []
        self.current_article: dict[str, Any] | None = None
        self.selected_link: str | None = None
        self._fetching_links: set[str] = set()
        self._translating_link: str | None = None
        self._settings_dialog: ft.AlertDialog | None = None

        # Controls
        self.search_field = ft.TextField(
            value=AppSettings.default_keyword,
            hint_text=t("keyword"),
            prefix_icon=ft.Icons.SEARCH,
            border_radius=12,
            dense=True,
            filled=True,
            on_submit=self._on_search_submit_async,
            expand=True,
        )
        self.search_button = ft.FilledButton(
            content=ft.Text(t("search")),
            icon=ft.Icons.SEARCH,
            on_click=self._on_search_click_async,
            height=44,
        )
        self.refresh_button = ft.IconButton(
            icon=ft.Icons.REFRESH_ROUNDED,
            tooltip=t("fetch_latest"),
            on_click=lambda e: self.page.run_task(self._fetch_latest),
        )
        self.settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS_OUTLINED,
            tooltip=t("settings"),
            on_click=self._open_settings,
        )
        self.news_list = ft.ListView(
            spacing=8,
            padding=0,
            expand=True,
        )
        self.list_header = ft.Text(
            value=t("query"),
            size=13,
            weight=ft.FontWeight.W_600,
        )
        self.search_hint = ft.Text(
            value=t("query_hint"),
            size=11,
            color=get_theme().get("muted", "#9aa0b4"),
        )
        self.article_title = ft.Text(
            value=t("no_article_selected"),
            weight=ft.FontWeight.W_700,
            size=22,
        )
        self.article_meta = ft.Text(value="", size=12)
        self.translation_mode_dropdown = ft.Dropdown(
            width=260,
            options=[
                ft.dropdown.Option("en_only", t("mode_en_only")),
                ft.dropdown.Option("en_zh", t("mode_en_zh")),
                ft.dropdown.Option("zh_only", t("mode_zh_only")),
                ft.dropdown.Option("zh_en", t("mode_zh_en")),
            ],
            value=AppSettings.translate_mode
            if AppSettings.translate_mode in {"en_zh", "zh_only", "zh_en"}
            else "en_only",
            
            dense=True,
        )
        self.translation_mode_dropdown.on_change = self._change_translate_mode
        self.auto_translate_switch = ft.Switch(
            label=t("auto_translate"),
            value=getattr(AppSettings, "auto_translate", True),
        )
        self.auto_translate_switch.on_change = self._toggle_auto_translate
        self.article_body = ft.Markdown(
            value="",
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        )
        self.article_status = ft.Text(value="", size=12)
        self.search_progress = ft.ProgressBar(visible=False, width=180)
        self.article_progress = ft.ProgressRing(visible=False)
        self.toast = ft.SnackBar(content=ft.Text(""),open=False)

        self.layout = ft.Container(
            expand=True,
            content=ft.Column(
                spacing=0,
                controls=[self._build_top_bar(), self._build_body()],
            ),
        )

        self._apply_theme()
        self.page.add(self.layout)
        self.page.overlay.append(self.toast)
        self.page.update()
        self.page.run_task(self._initial_search)

    # ------------------------------------------------------------------ Theme helpers
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
        palette = self._palette()
        self.page.theme_mode = (
            ft.ThemeMode.DARK if AppSettings.theme == "dark" else ft.ThemeMode.LIGHT
        )
        self.page.bgcolor = palette["bg"]
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=palette["accent"],
                secondary=palette["panel"],
            ),
            font_family="Segoe UI",
        )
        # Update shared colors
        self.search_field.fill_color = palette["panel"]
        self.search_field.border_color = palette["border"]
        self.search_field.cursor_color = palette["fg"]
        self.search_field.color = palette["fg"]
        self.list_header.color = palette["fg"]
        self.article_title.color = palette["fg"]
        self.article_meta.color = palette["muted"]
        self.article_status.color = palette["muted"]
        self.search_hint.color = palette["muted"]

    # ------------------------------------------------------------------ UI assembly
    def _build_top_bar(self) -> ft.Container:
        palette = self._palette()
        return ft.Container(
            bgcolor=palette["panel"],
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                bgcolor=palette["panel_alt"],
                                border_radius=12,
                                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                                content=ft.Text(
                                    t("title"),
                                    size=18,
                                    weight=ft.FontWeight.W_700,
                                    color=palette["fg"],
                                ),
                            )
                        ],
                    ),
                    self.search_field,
                    ft.Container(self.search_button, width=120),
                    ft.Container(
                        content=ft.Row(
                            spacing=6,
                            controls=[
                                self.search_progress,
                                self.refresh_button,
                                ft.IconButton(
                                    icon=ft.Icons.DARK_MODE_ROUNDED
                                    if AppSettings.theme == "dark"
                                    else ft.Icons.LIGHT_MODE,
                                    tooltip=t("toggle_theme"),
                                    on_click=self._toggle_theme,
                                ),
                                self.settings_button,
                            ],
                        )
                    ),
                ],
            ),
        )

    def _build_body(self) -> ft.Container:
        palette = self._palette()
        news_panel = ft.Container(
            width=360,
            bgcolor=palette["panel"],
            border=ft.border.only(right=ft.BorderSide(1, palette["border"])),
            padding=ft.padding.all(16),
            content=ft.Column(
                expand=True,
                spacing=12,
                controls=[
                    self.list_header,
                    self.search_hint,
                    ft.Container(
                        border_radius=12,
                        bgcolor=palette["panel_alt"],
                        padding=12,
                        content=self.news_list,
                        expand=True,
                    ),
                ],
            ),
        )

        article_panel = ft.Container(
            expand=True,
            bgcolor=palette["bg"],
            padding=ft.padding.only(left=18, right=18, top=12, bottom=18),
            content=ft.Column(
                expand=True,
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[self.article_title, self.article_meta],
                            ),
                            ft.Row(
                                spacing=12,
                                controls=[
                                    self.translation_mode_dropdown,
                                    self.auto_translate_switch,
                                    self.article_progress,
                                ],
                            ),
                        ],
                    ),
                    ft.Container(
                        bgcolor=palette["panel"],
                        border_radius=12,
                        padding=12,
                        expand=True,
                        content=ft.Column(
                            expand=True,
                            spacing=8,
                            controls=[
                                ft.Container(
                                    content=self.article_body,
                                    expand=True,
                                    border_radius=8,
                                ),
                            ],
                        ),
                    ),
                    self.article_status,
                ],
            ),
        )

        return ft.Container(
            expand=True,
            bgcolor=palette["bg"],
            content=ft.Row(
                expand=True,
                spacing=0,
                controls=[news_panel, article_panel],
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
        self.search_progress.visible = True
        self.article_status.value = ""
        self.page.update()

        cleaned_kw = (keyword or "").strip()
        try:
            rows = await _run_in_executor(lambda: query_news(keyword=cleaned_kw or None))
            self.news_rows = rows or []
            self._render_news_list(select_first=True)
            if not self.news_rows:
                self._show_toast(t("no_article_selected"))
        except Exception as e:
            self.article_status.value = f"Search failed: {e}"
            self._show_toast(f"Search failed: {e}")
        finally:
            self.search_button.disabled = False
            self.search_progress.visible = False
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
                bgcolor=palette["panel_alt"],
                border_radius=12,
                padding=12,
                ink=True,
                on_click=_click,
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text(
                            title,
                            weight=ft.FontWeight.W_700,
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
            async def _select_first():
                await self._handle_select(self.news_rows[0])

            asyncio.create_task(_select_first())

        self.news_list.update()

    def _update_list_highlight(self):
        palette = self._palette()
        for tile in self.news_list.controls:
            link = tile.data
            tile.bgcolor = (
                palette["panel"]
                if link == self.selected_link
                else palette["panel_alt"]
            )
            if isinstance(tile.content, ft.Column):
                for idx, child in enumerate(tile.content.controls):
                    if isinstance(child, ft.Text):
                        child.color = palette["fg"] if idx == 0 else palette["muted"]
        self.news_list.update()

    async def _handle_select(self, row: Iterable):
        title, source, region, published, link = row
        self.selected_link = link
        self._update_list_highlight()
        self.article_progress.visible = True
        self.article_status.value = t("loading_article")
        self.page.update()

        article = await _run_in_executor(lambda: get_article_by_link(link))
        if not article:
            self.article_title.value = title
            self.article_meta.value = f"{source} · {region} · {published}"
            self.article_body.value = t("loading_article")
            self.page.update()
            self.article_progress.visible = False
            return

        self.current_article = article
        self.article_meta.value = f"{source} · {region} · {published}"
        self.article_title.value = article.get("title") or title
        self._render_article()
        self.page.update()

        if not article.get("content_en") and link not in self._fetching_links:
            self._fetching_links.add(link)
            asyncio.create_task(self._fetch_content(article))
        else:
            self.article_progress.visible = False
            self.page.update()

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

        self.translation_mode_dropdown.value = mode if mode in {
            "en_zh", "zh_only", "zh_en"
        } else "en_only"
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
        self.article_progress.visible = False
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
            self.article_progress.visible = False
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
        self.article_status.value = t("auto_translate")
        self.article_progress.visible = True
        asyncio.create_task(self._translate_article(article))
        self.page.update()

    async def _translate_article(self, article: dict[str, Any]):
        link = article.get("link")
        try:
            zh_result = await _run_in_executor(
                lambda: translate_en_zh(article.get("content_en", ""), link=link)
            )
            content_to_save = zh_result.text
            if zh_result.note:
                content_to_save = (
                    f"[Partial translation] {zh_result.note}\n\n{zh_result.text}"
                )

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
            self.article_progress.visible = False
            self.page.update()

    # ------------------------------------------------------------------ Settings
    def _open_settings(self, e):
        print("=== SETTINGS CLICKED ===")

        palette = self._palette()  # ✅ 关键：定义 palette

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(t("settings_title")),
            content=ft.Column(
                spacing=16,
                controls=[
                    ft.Text(
                        t("appearance"),
                        weight=ft.FontWeight.W_600,
                        color=palette["muted"],  # ✅ 现在不会 NameError
                    ),
                    # 下面继续放你的 Switch / Dropdown / RadioGroup
                ],
            ),
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()



        def update_days(e2: ft.ControlEvent):
            try:
                AppSettings.default_days = int(
                    e2.control.value or AppSettings.default_days
                )
            except ValueError:
                e2.control.value = str(AppSettings.default_days)
                e2.control.update()

        # --- source dropdown（必须先创建，再绑定事件） ---
        source_dropdown = ft.Dropdown(
            label=t("source"),
            options=[
                ft.dropdown.Option("ALL"),
                ft.dropdown.Option("BBC"),
                ft.dropdown.Option("Guardian"),
                ft.dropdown.Option("Fox"),
            ],
            value=AppSettings.default_source,
        )

        source_dropdown.on_change = (
            lambda ev: setattr(AppSettings, "default_source", ev.control.value)
        )

        # --- defaults fields ---
        defaults_fields = ft.Column(
            spacing=10,
            controls=[
                ft.TextField(
                    label=t("keyword"),
                    value=AppSettings.default_keyword,
                    on_change=lambda ev: setattr(
                        AppSettings, "default_keyword", ev.control.value
                    ),
                ),
                ft.TextField(
                    label=t("days"),
                    value=str(AppSettings.default_days),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    on_change=update_days,
                ),
                source_dropdown,
            ],
        )


        async def _fetch_latest_click(ev):
            await self._fetch_latest()

        async def _clear_all_click(ev):
            await self._clear_all_data()

        action_buttons = ft.Row(
            controls=[
                ft.FilledButton(
                    content=ft.Text(t("fetch_latest")),
                    icon=ft.Icons.UPDATE,
                    on_click=_fetch_latest_click,
                ),
                ft.OutlinedButton(
                    content=ft.Text(t("clear_all_data")),
                    icon=ft.Icons.DELETE_SWEEP,
                    on_click=_clear_all_click,
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
                            content=ft.Text("save"),
                            icon=ft.Icons.SAVE_OUTLINED,
                            on_click=lambda _: self._save_settings(),
                        )
                    ],
                ),
            ],
            width=540,
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
        self.list_header.value = t("query")
        self.search_hint.value = t("query_hint")
        self.article_status.value = ""
        self.translation_mode_dropdown.options = [
            ft.dropdown.Option("en_only", t("mode_en_only")),
            ft.dropdown.Option("en_zh", t("mode_en_zh")),
            ft.dropdown.Option("zh_only", t("mode_zh_only")),
            ft.dropdown.Option("zh_en", t("mode_zh_en")),
        ]
        self.auto_translate_switch.label = t("auto_translate")
        self._rebuild_shell()

    # ------------------------------------------------------------------ Data actions
    async def _fetch_latest(self):
        self._show_toast(t("fetch_latest") + "...")
        try:
            await _run_in_executor(self._run_fetch_latest)
            await self._search(self.search_field.value.strip())
        finally:
            self.toast.open = False
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
        self.layout.content.controls[0] = self._build_top_bar()
        self.layout.content.controls[1] = self._build_body()
        self.page.controls.clear()
        self.page.add(self.layout)
        self._apply_theme()
        self._update_list_highlight()
        self._render_article()
        self.page.update()

    def _show_toast(self, message: str):
        self.toast.content = ft.Text(message)
        self.toast.open = True
        self.page.update()


# ================== APP ENTRY ==================
async def main(page: ft.Page):
    NewsDeskApp(page)


if __name__ == "__main__":
    ft.run(main)