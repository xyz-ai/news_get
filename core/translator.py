from googletrans import Translator

translator = Translator()
_cache = {}


def translate(text):
    if text in _cache:
        return _cache[text]

    result = translator.translate(text, src="en", dest="zh-cn").text
    _cache[text] = result
    return result
