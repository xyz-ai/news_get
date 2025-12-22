# translator.py
from googletrans import Translator

_translator = Translator()


def translate_en_zh(text: str) -> str:
    if not text.strip():
        return text
    try:
        return _translator.translate(
            text, src="en", dest="zh-cn"
        ).text
    except Exception:
        return text
