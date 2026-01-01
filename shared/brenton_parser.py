"""
Brenton.tex parser utility for extracting verses and words.

Provides a shared parser that eliminates duplicated parsing logic
across multiple scripts that analyze Brenton's Septuagint text.
"""

import re
from dataclasses import dataclass
from typing import Iterator, Optional

from shared.greek_utils import normalize_text, extract_greek_words


@dataclass
class VerseContext:
    """Context for a single line in Brenton.tex."""
    line_num: int
    line: str                      # Full normalized line (stripped)
    book: Optional[str]
    chapter: Optional[int]
    verse: Optional[str]           # String to support "1d", "2a" etc.
    verse_ref: str                 # "ΓΕΝΕΣΙΣ 1:1" or ""
    greek_words: list              # Extracted words with diacritics
    has_complete_ref: bool         # True if book, chapter, verse all set


class BrentonParser:
    """Parser for Brenton.tex that yields verse context for each line.

    Usage:
        parser = BrentonParser('../input/Brenton.tex')
        for ctx in parser.parse():
            if not ctx.has_complete_ref:
                continue
            # Process ctx.greek_words, ctx.verse_ref, etc.
    """

    def __init__(self, bible_path: str):
        self.bible_path = bible_path

    def parse(self) -> Iterator[VerseContext]:
        """Iterate through Brenton.tex, yielding VerseContext for each line.

        Tracks book/chapter/verse state across lines. The parser handles:
        - \\biblebook{BOOK_NAME} - sets current book, resets chapter/verse
        - \\ch{N} - sets current chapter, resets verse
        - \\lettrine - indicates chapter 1 if no chapter set yet
        - \\vs{N} - sets current verse

        Yields:
            VerseContext for each line with current parsing state.
        """
        current_book = None
        current_chapter = None
        current_verse = None

        print(f"Processing {self.bible_path}...")

        with open(self.bible_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = normalize_text(line)

                # Track book
                book_match = re.search(r'\\biblebook\{([^}]+)\}', line)
                if book_match:
                    current_book = book_match.group(1)
                    current_chapter = None
                    current_verse = None

                # Track chapter
                ch_match = re.search(r'\\ch\{(\d+)\}', line)
                if ch_match:
                    current_chapter = int(ch_match.group(1))
                    current_verse = "1"  # Verse 1 is implied after chapter

                # Also check for lettrine (start of chapter 1)
                if '\\lettrine' in line and current_chapter is None:
                    current_chapter = 1
                    current_verse = "1"  # First verse of first chapter

                # Track verse (supports alpha suffixes like "1d", "2a")
                vs_match = re.search(r'\\vs\{(\d+[a-z]*)\}', line)
                if vs_match:
                    current_verse = vs_match.group(1)  # Keep as string

                # Build verse reference
                has_complete_ref = all([current_book, current_chapter, current_verse])
                verse_ref = ""
                if has_complete_ref:
                    verse_ref = f"{current_book} {current_chapter}:{current_verse}"

                # Extract Greek words
                greek_words = extract_greek_words(line)

                yield VerseContext(
                    line_num=line_num,
                    line=line.strip(),
                    book=current_book,
                    chapter=current_chapter,
                    verse=current_verse,
                    verse_ref=verse_ref,
                    greek_words=greek_words,
                    has_complete_ref=has_complete_ref
                )
