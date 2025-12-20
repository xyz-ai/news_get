LANG = "zh"

TEXT = {
    "zh": {
        "title": "新闻系统",
        "query": "查询",
        "settings": "设置",
        "source": "来源",
        "region": "地区",
        "keyword": "关键词",
        "time_range": "时间范围",
        "translate": "翻译为中文",
        "search": "搜索",
        "theme": "主题",
        "language": "语言",
        "dark": "深色",
        "light": "浅色",
        "english": "英文",
        "chinese": "中文",
    },
    "en": {
        "title": "News System",
        "query": "Query",
        "settings": "Settings",
        "source": "Source",
        "region": "Region",
        "keyword": "Keyword",
        "time_range": "Time Range",
        "translate": "Translate to Chinese",
        "search": "Search",
        "theme": "Theme",
        "language": "Language",
        "dark": "Dark",
        "light": "Light",
        "english": "English",
        "chinese": "Chinese",
    },
}


def t(key):
    return TEXT[LANG].get(key, key)


def set_language(lang):
    global LANG
    LANG = lang
