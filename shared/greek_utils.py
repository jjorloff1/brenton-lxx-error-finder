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


# Greek accent combining characters (used for accent comparison filtering)
GREEK_ACCENTS = {
    0x0300: 'GRAVE',      # COMBINING GRAVE ACCENT (varia)
    0x0301: 'ACUTE',      # COMBINING ACUTE ACCENT (oxia/tonos)
    0x0342: 'CIRCUMFLEX', # COMBINING GREEK PERISPOMENI
}


def extract_accent_info(word):
    """Extract accent information from a Greek word.

    Args:
        word: Greek word (Unicode string)

    Returns:
        List of tuples: (base_char_position, accent_type, base_char)
        where:
        - base_char_position: index in the diacritic-stripped version
        - accent_type: 'GRAVE', 'ACUTE', or 'CIRCUMFLEX'
        - base_char: the base character that carries the accent

    Example:
        extract_accent_info('αὐτὸν') -> [(3, 'GRAVE', 'ο')]
        extract_accent_info('αὐτοῦ') -> [(4, 'CIRCUMFLEX', 'υ')]
    """
    # Normalize to NFC first, then decompose to NFD
    nfd = unicodedata.normalize('NFD', normalize_text(word))

    accents = []
    base_char_pos = -1
    current_base = None

    for char in nfd:
        cat = unicodedata.category(char)
        if cat != 'Mn':  # Base character (not combining mark)
            base_char_pos += 1
            current_base = char
        else:
            code = ord(char)
            if code in GREEK_ACCENTS:
                accents.append((base_char_pos, GREEK_ACCENTS[code], current_base))

    return accents


def compare_accents(word1, word2):
    """Compare accents between two Greek words.

    Args:
        word1: First Greek word (typically Brenton)
        word2: Second Greek word (typically Rahlfs)

    Returns:
        Tuple of (result, accents1, accents2) where result is one of:
        - 'same': accents are identical (type and position)
        - 'different_position': accent on different characters
        - 'different_type': same position, different type
        - 'word1_missing': word1 has no accent, word2 does
        - 'word2_missing': word1 has accent, word2 doesn't
        - 'both_none': neither word has an accent
    """
    acc1 = extract_accent_info(word1)
    acc2 = extract_accent_info(word2)

    if not acc1 and not acc2:
        return ('both_none', acc1, acc2)

    if not acc1:
        return ('word1_missing', acc1, acc2)

    if not acc2:
        return ('word2_missing', acc1, acc2)

    # Compare primary accent (most Greek words have only one)
    pos1, type1, _ = acc1[0]
    pos2, type2, _ = acc2[0]

    if pos1 != pos2:
        return ('different_position', acc1, acc2)

    if type1 != type2:
        return ('different_type', acc1, acc2)

    return ('same', acc1, acc2)


def should_filter_by_accent(brenton_word, rahlfs_word):
    """Determine if a word pair should be filtered based on accent differences.

    Filtering logic:
    - FILTER (return True): Different accent position -> likely variant
    - FILTER (return True): Different type involving circumflex -> likely variant
    - KEEP (return False): Same accents -> needs examination
    - KEEP (return False): Same position, acute/grave switch -> needs examination
    - KEEP (return False): Brenton missing accent -> potential transcription error
    - KEEP (return False): Both have no accent -> can't filter by accent
    - KEEP (return False): Rahlfs missing accent -> unusual, keep for review

    Args:
        brenton_word: Word from Brenton text (may have OCR errors)
        rahlfs_word: Word from Rahlfs text (reference)

    Returns:
        True if the pair should be filtered out (likely valid variant)
        False if the pair should be kept (needs examination)
    """
    result, acc1, acc2 = compare_accents(brenton_word, rahlfs_word)

    # Filter out when accent position differs -> likely valid variant
    if result == 'different_position':
        return True

    # For different types at same position, check if it's acute/grave switch
    if result == 'different_type':
        # Get the accent types
        type1 = acc1[0][1] if acc1 else None
        type2 = acc2[0][1] if acc2 else None
        # Keep acute/grave switches (they're essentially the same accent)
        if {type1, type2} == {'ACUTE', 'GRAVE'}:
            return False
        # Filter other type differences (involving circumflex)
        return True

    # Keep (return False) in all other cases:
    # - 'same': Same accents, needs examination
    # - 'word1_missing': Brenton lost accent, potential OCR error
    # - 'word2_missing': Unusual case, keep for review
    # - 'both_none': Can't determine from accents, keep
    return False


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
