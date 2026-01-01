#!/usr/bin/env python3
"""
Detect misplaced grave accents in Brenton Septuagint.

In Greek, the grave accent should only appear on the ultimate (final) syllable
of a word. A grave accent on a non-final vowel indicates a likely transcription
error where an acute was mistakenly rendered as a grave.

This script scans Brenton.tex and flags any word where a grave accent appears
on a vowel that is not the last vowel in the word.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

# Add parent directory to path to import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.greek_utils import (
    normalize_text,
    extract_greek_words,
    extract_accent_info,
    strip_diacritics
)

# Greek vowels (accents only appear on vowels)
GREEK_VOWELS = set('αεηιουωΑΕΗΙΟΥΩ')


def find_last_vowel_position(word):
    """Find the position of the last vowel in a diacritic-stripped word.

    Args:
        word: Greek word (will be stripped of diacritics internally)

    Returns:
        Position (0-indexed) of the last vowel, or -1 if no vowel found.
    """
    stripped = strip_diacritics(word)
    for i in range(len(stripped) - 1, -1, -1):
        if stripped[i] in GREEK_VOWELS:
            return i
    return -1


def has_misplaced_grave(word):
    """Check if word has a grave accent on a non-ultimate vowel.

    In Greek, the grave accent should only appear on the final syllable
    (specifically on the last vowel). A grave on any earlier vowel is
    likely a transcription error.

    Args:
        word: Greek word with diacritics

    Returns:
        Tuple of (position, base_char) if misplaced grave found, None otherwise.
    """
    accents = extract_accent_info(word)
    last_vowel_pos = find_last_vowel_position(word)

    if last_vowel_pos < 0:
        return None  # No vowel in word (shouldn't happen in Greek)

    for pos, accent_type, base_char in accents:
        if accent_type == 'GRAVE' and pos < last_vowel_pos:
            return (pos, base_char)
    return None


def fix_misplaced_grave(word, grave_position):
    """Replace misplaced grave accent with acute.

    Args:
        word: Greek word with misplaced grave accent
        grave_position: Position (0-indexed) of the misplaced grave

    Returns:
        Word with the misplaced grave converted to acute.
    """
    import unicodedata

    # Normalize to NFD to separate base chars from combining marks
    nfd = unicodedata.normalize('NFD', normalize_text(word))

    result = []
    base_char_pos = -1

    for char in nfd:
        cat = unicodedata.category(char)
        if cat != 'Mn':  # Base character
            base_char_pos += 1
            result.append(char)
        else:
            # Check if this is the grave accent at the misplaced position
            if ord(char) == 0x0300 and base_char_pos == grave_position:
                # Replace grave (0x0300) with acute (0x0301)
                result.append('\u0301')
            else:
                result.append(char)

    return unicodedata.normalize('NFC', ''.join(result))


def process_brenton_file(brenton_path):
    """Process Brenton.tex and find misplaced grave accents.

    Args:
        brenton_path: Path to Brenton.tex file

    Returns:
        List of error dicts with verse_ref, line_num, word, position, full_line
    """
    errors = []

    current_book = None
    current_chapter = None
    current_verse = None

    print(f"Processing {brenton_path}...")

    with open(brenton_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = normalize_text(line)

            # Track book
            book_match = re.search(r'\\biblebook\{([^}]+)\}', line)
            if book_match:
                current_book = book_match.group(1)
                current_chapter = None
                current_verse = None
                continue

            # Track chapter
            ch_match = re.search(r'\\ch\{(\d+)\}', line)
            if ch_match:
                current_chapter = int(ch_match.group(1))
                current_verse = None

            # Also check for lettrine (start of chapter)
            if '\\lettrine' in line and current_chapter is None:
                current_chapter = 1

            # Track verse
            vs_match = re.search(r'\\vs\{(\d+)\}', line)
            if vs_match:
                current_verse = int(vs_match.group(1))

            # Skip if we don't have complete reference
            if not all([current_book, current_chapter, current_verse]):
                continue

            # Build verse reference
            verse_ref = f"{current_book} {current_chapter}:{current_verse}"

            # Extract words from this line
            words = extract_greek_words(line)
            if not words:
                continue

            # Check each word for misplaced grave
            for word in words:
                misplaced = has_misplaced_grave(word)
                if misplaced:
                    pos, base_char = misplaced
                    errors.append({
                        'line_num': line_num,
                        'verse_ref': verse_ref,
                        'word': word,
                        'suggested_fix': fix_misplaced_grave(word, pos),
                        'full_line': line.strip()
                    })

    return errors


def write_errors_tsv(errors, output_path):
    """Write detected errors to TSV file."""
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow([
            'Line Number', 'Verse Reference', 'Word', 'Suggested Fix', 'Full Line'
        ])
        for error in errors:
            writer.writerow([
                error['line_num'],
                error['verse_ref'],
                error['word'],
                error['suggested_fix'],
                error['full_line']
            ])
    print(f"Wrote {len(errors)} errors to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Detect misplaced grave accents in Brenton Septuagint'
    )
    parser.add_argument(
        '--brenton',
        default='../check_missing_words_for_typos/input/Brenton.tex',
        help='Path to Brenton.tex source file'
    )
    parser.add_argument(
        '--output',
        default='output/misplaced_graves.tsv',
        help='Output TSV file path'
    )

    args = parser.parse_args()

    # Process file
    errors = process_brenton_file(args.brenton)

    # Write output
    write_errors_tsv(errors, args.output)

    # Print summary
    print(f"\nSummary:")
    print(f"  Total misplaced grave accents found: {len(errors)}")


if __name__ == '__main__':
    main()
