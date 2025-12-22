from core.settings import AppSettings

TEXT = {
    "en": {
        "title": "News Desk",
        "settings": "Settings",
        "appearance": "Appearance",
        "toggle_theme": "Toggle Theme (Dark / Light)",
        "language": "Language",
        "font_size": "Font Size",
        "query": "Query",
        "keyword": "Keyword",
        "search": "Search",
        "default_params": "Default Query Parameters",
        "days": "Days",
        "source": "Source",
        "save": "Save",
        "query_hint": "More filters are coming soon. Currently searching titles by keyword.",
        "panel_width": "Panel width",
        "translation_mode": "Translation display",
        "mode_en_zh": "English → Chinese",
        "mode_zh_only": "Chinese only",
        "mode_zh_en": "Chinese → English",
    },
    "zh": {
        "title": "新闻阅读器",
        "settings": "设置",
        "appearance": "外观",
        "toggle_theme": "切换主题（深色 / 浅色）",
        "language": "语言",
        "font_size": "字体大小",
        "query": "查询",
        "keyword": "关键词",
        "search": "搜索",
        "default_params": "默认查询参数",
        "days": "天数",
        "source": "来源",
        "save": "保存",
        "query_hint": "更多筛选项即将上线，目前根据关键词在标题中搜索。",
        "panel_width": "调节侧边栏宽度",
        "translation_mode": "翻译显示方式",
        "mode_en_zh": "英文在前，中文在后",
        "mode_zh_only": "仅显示中文",
        "mode_zh_en": "中文在前，英文在后",
    },
}


def t(key: str) -> str:
    lang = AppSettings.language
    return TEXT.get(lang, TEXT["en"]).get(key, key)
