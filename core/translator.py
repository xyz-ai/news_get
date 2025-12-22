# translator.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from googletrans import Translator

MAX_CHUNK_LENGTH = 3000

_translator = Translator()


@dataclass
class TranslationError(Exception):
    message: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


def split_text(text: str, max_len: int = MAX_CHUNK_LENGTH) -> List[str]:
    """
    Split text into chunks that are safe for translation APIs.

    We prefer to split on newlines or spaces to avoid cutting sentences in half.
    Each chunk is guaranteed to be non-empty and <= max_len.
    """

    normalized = text.strip()
    if not normalized:
        return []

    chunks: List[str] = []
    start = 0
    length = len(normalized)

    while start < length:
        end = min(start + max_len, length)

        if end < length:
            split_at = normalized.rfind("\n", start, end)
            if split_at <= start:
                split_at = normalized.rfind(" ", start, end)
            if split_at <= start:
                split_at = end
        else:
            split_at = end

        chunk = normalized[start:split_at].strip()
        if not chunk:
            raise TranslationError("Failed to split text into non-empty chunks")

        chunks.append(chunk)

        # Advance cursor past any whitespace to avoid empty segments
        start = split_at
        while start < length and normalized[start].isspace():
            start += 1

    return chunks


def _translate_chunk(text: str) -> str:
    translated = _translator.translate(text, src="en", dest="zh-cn").text
    if not translated or not translated.strip():
        raise TranslationError("Empty translation result")
    if translated.strip() == text.strip():
        raise TranslationError("Translation did not change source text")
    return translated


def translate_en_zh(text: str) -> str:
    """
    Translate English text to Chinese in safe chunks.

    Raises TranslationError on any failure so callers can decide whether to
    cache the result. Partial translations are never returned.
    """

    chunks = split_text(text, max_len=MAX_CHUNK_LENGTH)
    if not chunks:
        raise TranslationError("No content to translate")

    translated_parts = []
    for chunk in chunks:
        translated_parts.append(_translate_chunk(chunk))

    translated_text = "\n\n".join(translated_parts)
    if not translated_text.strip():
        raise TranslationError("Combined translation is empty")

    if translated_text.strip() == text.strip():
        raise TranslationError("Translated text matches source")

    return translated_text
