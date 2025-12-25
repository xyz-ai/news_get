from __future__ import annotations

from dataclasses import dataclass
from typing import List
from urllib.parse import urlparse

MAX_CHUNK_LENGTH = 3000


# =========================
# Exceptions & Results
# =========================

@dataclass
class TranslationError(Exception):
    message: str

    def __str__(self) -> str:  # pragma: no cover
        return self.message


@dataclass
class TranslationResult:
    text: str
    translated_chunks: int
    failed_chunks: int
    total_chunks: int
    note: str | None = None

    @property
    def failure_rate(self) -> float:
        if self.total_chunks == 0:
            return 0.0
        return self.failed_chunks / self.total_chunks

    @property
    def translation_status(self) -> str:
        if self.translated_chunks == 0:
            return "failed"
        return "success" if self.failure_rate <= 0.2 else "failed"


# =========================
# Utilities
# =========================

def split_text(text: str, max_len: int = MAX_CHUNK_LENGTH) -> List[str]:
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

        start = split_at
        while start < length and normalized[start].isspace():
            start += 1

    return chunks


def _is_bbc_link(link: str | None) -> bool:
    if not link:
        return False
    try:
        netloc = urlparse(link).netloc.lower()
    except Exception:
        netloc = link.lower()
    return "bbc." in netloc or netloc.endswith(("bbc.com", "bbc.co.uk"))


def _clean_bbc_text(text: str) -> str:
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or len(line.split()) < 4:
            continue
        if line.startswith(("This video", "BBC News")):
            continue
        lower_line = line.lower()
        if "click here" in lower_line or "related topics" in lower_line:
            continue
        cleaned_lines.append(line)
    return "\n\n".join(cleaned_lines)


# =========================
# Translation Core
# =========================

def _get_translator():
    """
    Try to lazily create a googletrans Translator.
    Returns None if not available.
    """
    try:
        from googletrans import Translator  # type: ignore
        return Translator()
    except Exception:
        return None


def _translate_chunk(translator, text: str) -> str:
    translated = translator.translate(text, src="en", dest="zh-cn").text
    if not translated or not translated.strip():
        raise TranslationError("Empty translation result")
    if translated.strip() == text.strip():
        raise TranslationError("Translation did not change source text")
    return translated


def translate_en_zh(text: str, *, link: str | None = None) -> TranslationResult:
    """
    Translate English text to Chinese.

    If translation capability is unavailable (e.g. Android APK),
    this function will gracefully fall back to returning English text.
    """

    if not text or not text.strip():
        return TranslationResult(
            text="",
            translated_chunks=0,
            failed_chunks=0,
            total_chunks=0,
            note="Empty source text",
        )

    if link and "/news/videos/" in link:
        return TranslationResult(
            text=text,
            translated_chunks=0,
            failed_chunks=0,
            total_chunks=0,
            note="Video page – translation skipped",
        )

    source_text = text
    if _is_bbc_link(link):
        cleaned = _clean_bbc_text(text)
        if cleaned:
            source_text = cleaned

    chunks = split_text(source_text, max_len=MAX_CHUNK_LENGTH)
    if not chunks:
        return TranslationResult(
            text=text,
            translated_chunks=0,
            failed_chunks=0,
            total_chunks=0,
            note="No content to translate",
        )

    translator = _get_translator()

    # 🚨 核心降级点：没有翻译能力
    if translator is None:
        return TranslationResult(
            text=source_text,
            translated_chunks=0,
            failed_chunks=len(chunks),
            total_chunks=len(chunks),
            note="Translation unavailable on this platform",
        )

    translated_parts: list[str] = []
    translated_chunks = 0
    failed_chunks = 0

    for chunk in chunks:
        try:
            translated_parts.append(_translate_chunk(translator, chunk))
            translated_chunks += 1
        except TranslationError:
            translated_parts.append(chunk)
            failed_chunks += 1
        except Exception as e:
            translated_parts.append(chunk)
            failed_chunks += 1

    translated_text = "\n\n".join(translated_parts)

    note = None
    if failed_chunks:
        note = f"{failed_chunks}/{len(chunks)} chunks kept in English"

    return TranslationResult(
        text=translated_text,
        translated_chunks=translated_chunks,
        failed_chunks=failed_chunks,
        total_chunks=len(chunks),
        note=note,
    )
