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
        "query": "Query",
        "keyword": "Keyword",
        "search": "Search",
        "default_params": "Default Query Parameters",
        "days": "Days",
        "source": "Source",
        "en": "Auto translate to Chinese",
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
        "query": "查询",
        "keyword": "关键词",
        "search": "搜索",
        "default_params": "默认查询参数",
        "days": "天数",
        "source": "来源",
        "zh": "自动翻译为中文",
    },
    "translation_mode": {
    "en": "Translation display",
    "zh": "翻译显示方式",
    },
    "mode_en_zh": {
        "en": "English → Chinese",
        "zh": "英文在前，中文在后",
    },
    "mode_zh_only": {
        "en": "Chinese only",
        "zh": "仅显示中文",
    },
    "mode_zh_en": {
        "en": "Chinese → English",
        "zh": "中文在前，英文在后",
    },

}


def t(key: str) -> str:
    lang = AppSettings.language
    return TEXT.get(lang, TEXT["en"]).get(key, key)
