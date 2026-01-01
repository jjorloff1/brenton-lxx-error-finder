"""
Greek text processing utilities for the Brenton LXX Error Finder.

Provides functions for:
- Unicode normalization
- Diacritical mark handling
- Greek word extraction from LaTeX
- Loading accepted words and corrections
"""

import re
import unicodedata
import csv


def normalize_text(text):
    """Normalize Greek text using NFC normalization."""
    return unicodedata.normalize("NFC", text)


def strip_diacritics(text):
    """Remove diacritical marks and accents from Greek text."""
    # First apply NFC normalization for consistency
    text = normalize_text(text)
    # Then decompose to NFD (separates base chars from combining marks)
    text = unicodedata.normalize('NFD', text)
    # Remove combining characters (accents, breathing marks, etc.)
    stripped = ''.join(
        char for char in text
        if unicodedata.category(char) != 'Mn'
    )
    # Normalize back to NFC for consistent comparison
    return unicodedata.normalize('NFC', stripped)


def normalize_for_comparison(text):
    """Normalize text for comparison purposes.
    - Strips spaces (for compound word matching)
    - Replaces ς with σ when not at the end of the word
    """
    # Remove spaces
    text = text.replace(' ', '')

    # Replace ς with σ when it's not the last character
    # Process from left to right, checking if ς is followed by more characters
    result = []
    for i, char in enumerate(text):
        if char == 'ς' and i < len(text) - 1:
            result.append('σ')
        else:
            result.append(char)

    return ''.join(result)


def extract_greek_words(line):
    """Extract Greek words from a line, excluding LaTeX commands."""
    words = []

    # Check for \lettrine macro at the beginning of a book
    # There are two patterns:
    # 1. With \textcolor: \lettrine[...]{\textcolor{...}{Φ}}{ΙΛΟΣΟΦΩΤΑΤΟΝ}
    # 2. Without \textcolor: \lettrine[...]{Κ}{ΑΙ}

    # Try pattern with \textcolor first (more specific)
    lettrine_pattern_textcolor = r'\\lettrine\[[^\]]*\]\{\\textcolor\{[^}]+\}\{([^}]+)\}\}\{([^}]*)\}'
    lettrine_match = re.search(lettrine_pattern_textcolor, line)

    if not lettrine_match:
        # Try simple pattern without \textcolor
        lettrine_pattern_simple = r'\\lettrine\[[^\]]*\]\{([^}]+)\}\{([^}]*)\}'
        lettrine_match = re.search(lettrine_pattern_simple, line)

    if lettrine_match:
        # Extract the first character
        first_char = lettrine_match.group(1)
        # Extract the rest of the word from the second group
        rest_of_word = lettrine_match.group(2)

        # Combine and lowercase the first word
        if rest_of_word.strip():
            first_word = (first_char + rest_of_word).lower()
        else:
            # Single character word
            first_word = first_char.lower()

        words.append(normalize_text(first_word))

        # Remove the \lettrine command from the line for further processing
        line = line[:lettrine_match.start()] + line[lettrine_match.end():]

    # Remove remaining LaTeX commands and their contents
    line = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', line)
    line = re.sub(r'\\[a-zA-Z]+', '', line)

    # Match Greek words (unicode Greek range)
    # Greek range: \u0370-\u03FF (basic Greek), \u1F00-\u1FFF (extended Greek)
    greek_pattern = r'[\u0370-\u03FF\u1F00-\u1FFF]+'
    remaining_words = re.findall(greek_pattern, line)

    words.extend([normalize_text(word) for word in remaining_words])

    return words


def load_accepted_words(filepath):
    """Load accepted words from a text file (one word per line)."""
    print(f"Opening accepted words file: {filepath}")
    words = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            print(f"Successfully opened {filepath}")
            line_count = 0
            for line in f:
                line_count += 1
                word = line.strip()
                if word and not word.startswith('#'):  # Skip empty lines and comments
                    # Normalize and strip diacritics for comparison
                    normalized = strip_diacritics(normalize_text(word).lower())
                    words.add(normalized)
            print(f"Finished reading {filepath} ({line_count} lines, {len(words)} words loaded)")
    except FileNotFoundError:
        print(f"Note: Accepted words file '{filepath}' not found. Continuing without it.")
    except Exception as e:
        print(f"Error loading accepted words from {filepath}: {e}")
    return words


def load_already_examined(filepath):
    """Load already examined word changes from a TSV file.
    Returns dict mapping (verse_ref, normalized_word) -> corrected_word.
    """
    print(f"Opening already examined file: {filepath}")
    examined = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            print(f"Successfully opened {filepath}")
            reader = csv.reader(f, delimiter='\t')
            row_count = 0
            for row in reader:
                row_count += 1
                if len(row) >= 3:
                    verse_ref = normalize_text(row[0].strip())
                    original_word = normalize_text(row[1].strip())
                    corrected_word = normalize_text(row[2].strip())
                    # Normalize and strip diacritics for comparison
                    normalized_word = strip_diacritics(original_word.lower())
                    key = (verse_ref, normalized_word)
                    examined[key] = corrected_word
            print(f"Finished reading {filepath} ({row_count} rows, {len(examined)} word changes loaded)")
    except FileNotFoundError:
        print(f"Note: Already examined file '{filepath}' not found. Continuing without it.")
    except Exception as e:
        print(f"Error loading already examined from {filepath}: {e}")
    return examined
