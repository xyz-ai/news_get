import requests
from dataclasses import dataclass
from typing import List
from urllib.parse import urlparse

LIBRE_URL = "https://libretranslate.com/translate"
MAX_CHUNK_LENGTH = 3000


@dataclass
class TranslationError(Exception):
    message: str

    def __str__(self):
        return self.message


@dataclass
class TranslationResult:
    text: str
    translated_chunks: int
    failed_chunks: int
    total_chunks: int
    note: str | None = None


def split_text(text: str, max_len: int = MAX_CHUNK_LENGTH) -> List[str]:
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_len, len(text))
        split_at = text.rfind("\n", start, end)
        if split_at == -1:
            split_at = text.rfind(" ", start, end)
        if split_at == -1:
            split_at = end

        chunk = text[start:split_at].strip()
        if chunk:
            chunks.append(chunk)
        start = split_at

    return chunks


def _is_bbc_link(link: str | None) -> bool:
    if not link:
        return False
    netloc = urlparse(link).netloc.lower()
    return "bbc." in netloc


def _clean_bbc_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if len(line.split()) < 4:
            continue
        if line.lower().startswith(("this video", "bbc news")):
            continue
        lines.append(line)
    return "\n\n".join(lines)


def _translate_chunk(chunk: str) -> str:
    r = requests.post(
        LIBRE_URL,
        json={
            "q": chunk,
            "source": "en",
            "target": "zh",
            "format": "text",
        },
        timeout=20,
    )
    if r.status_code != 200:
        raise TranslationError(f"HTTP {r.status_code}")

    data = r.json()
    translated = data.get("translatedText", "")
    if not translated.strip():
        raise TranslationError("Empty translation")

    return translated


def translate_en_zh(text: str, *, link: str | None = None) -> TranslationResult:
    if link and "/news/videos/" in link:
        raise TranslationError("Video page – translation not supported")

    source_text = text
    if _is_bbc_link(link):
        cleaned = _clean_bbc_text(text)
        if cleaned:
            source_text = cleaned

    chunks = split_text(source_text)
    if not chunks:
        raise TranslationError("No content to translate")

    translated_parts = []
    translated_chunks = 0
    failed_chunks = 0

    for chunk in chunks:
        try:
            translated_parts.append(_translate_chunk(chunk))
            translated_chunks += 1
        except Exception:
            translated_parts.append(chunk)
            failed_chunks += 1

    if translated_chunks == 0:
        raise TranslationError("All chunks failed")

    note = None
    if failed_chunks:
        note = f"{failed_chunks}/{len(chunks)} chunks kept in English"

    return TranslationResult(
        text="\n\n".join(translated_parts),
        translated_chunks=translated_chunks,
        failed_chunks=failed_chunks,
        total_chunks=len(chunks),
        note=note,
    )
