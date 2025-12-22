# translator.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List
from urllib.parse import urlparse

from googletrans import Translator

MAX_CHUNK_LENGTH = 3000

_translator = Translator()


@dataclass
class TranslationError(Exception):
    message: str

    def __str__(self) -> str:  # pragma: no cover - trivial
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
        """
        success: at least one chunk translated AND failure rate <= 20%
        failed: otherwise
        """
        if self.translated_chunks == 0:
            return "failed"
        return "success" if self.failure_rate <= 0.2 else "failed"


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


def _is_bbc_link(link: str | None) -> bool:
    if not link:
        return False

    try:
        netloc = urlparse(link).netloc.lower()
    except Exception:
        netloc = link.lower()

    return "bbc." in netloc or netloc.endswith("bbc.com") or netloc.endswith("bbc.co.uk")


def _clean_bbc_text(text: str) -> str:
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if len(line.split()) < 4:
            continue

        if line.startswith(("This video", "BBC News")):
            continue

        lower_line = line.lower()
        if "click here" in lower_line or "related topics" in lower_line:
            continue

        cleaned_lines.append(line)

    return "\n\n".join(cleaned_lines)


def _translate_chunk(text: str) -> str:
    translated = _translator.translate(text, src="en", dest="zh-cn").text
    if not translated or not translated.strip():
        raise TranslationError("Empty translation result")
    if translated.strip() == text.strip():
        raise TranslationError("Translation did not change source text")
    return translated


def translate_en_zh(text: str, *, link: str | None = None) -> TranslationResult:
    """
    Translate English text to Chinese in safe chunks.

    Allows partial success: failed chunks are replaced with the original
    English text. TranslationError is raised for API-level failures or when
    no chunks can be translated at all.
    """

    if link and "/news/videos/" in link:
        raise TranslationError("Video page – translation not supported")

    source_text = text
    if _is_bbc_link(link):
        cleaned = _clean_bbc_text(text)
        if cleaned:
            source_text = cleaned

    chunks = split_text(source_text, max_len=MAX_CHUNK_LENGTH)
    if not chunks:
        raise TranslationError("No content to translate")

    translated_parts: list[str] = []
    translated_chunks = 0
    failed_chunks = 0

    for chunk in chunks:
        try:
            translated_parts.append(_translate_chunk(chunk))
            translated_chunks += 1
        except TranslationError:
            translated_parts.append(chunk)
            failed_chunks += 1
        except Exception as e:
            raise TranslationError(f"Translation API error: {e}")

    if translated_chunks == 0:
        raise TranslationError("No chunks translated")

    translated_text = "\n\n".join(translated_parts)
    if not translated_text.strip():
        raise TranslationError("Combined translation is empty")

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
