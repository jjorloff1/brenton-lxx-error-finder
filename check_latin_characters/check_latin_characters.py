#!/usr/bin/env python3
"""
Detect Latin characters in Greek words in Brenton Septuagint.

A common OCR error is confusion between visually similar Latin and Greek
characters. For example, Latin 'p' looks identical to Greek 'ρ' (rho),
and Latin 'A' looks like Greek 'Α' (Alpha).

This script scans Brenton.tex and word_corrections.tsv, flagging any Greek
word that contains Latin characters, which indicates an OCR error.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

# Add parent directory to path to import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.brenton_parser import BrentonParser
from shared.greek_utils import normalize_text

# Latin characters mapped to Greek equivalents for suggested fixes
# Includes both visually similar characters (OCR errors) and
# keyboard-based mappings (typing errors from wrong keyboard layout)
LATIN_TO_GREEK = {
    # Uppercase - visually similar
    'A': 'Α',  # Alpha (visual)
    'B': 'Β',  # Beta (visual)
    'E': 'Ε',  # Epsilon (visual)
    'H': 'Η',  # Eta (visual)
    'I': 'Ι',  # Iota (visual)
    'K': 'Κ',  # Kappa (visual)
    'M': 'Μ',  # Mu (visual)
    'N': 'Ν',  # Nu (visual)
    'O': 'Ο',  # Omicron (visual)
    'P': 'Ρ',  # Rho (visual)
    'T': 'Τ',  # Tau (visual)
    'X': 'Χ',  # Chi (visual)
    'Y': 'Υ',  # Upsilon (visual)
    'Z': 'Ζ',  # Zeta (visual)
    # Uppercase - keyboard layout (Greek keyboard position)
    'C': 'Ψ',  # Psi (keyboard)
    'D': 'Δ',  # Delta (keyboard)
    'F': 'Φ',  # Phi (keyboard)
    'G': 'Γ',  # Gamma (keyboard)
    'J': 'Ξ',  # Xi (keyboard)
    'L': 'Λ',  # Lambda (keyboard)
    'Q': ';',  # not a letter on Greek keyboard
    'R': 'Ρ',  # Rho (keyboard)
    'S': 'Σ',  # Sigma (keyboard)
    'U': 'Θ',  # Theta (keyboard)
    'V': 'Ω',  # Omega (keyboard)
    'W': 'Σ',  # final Sigma (keyboard)
    # Lowercase - visually similar
    'a': 'α',  # alpha (visual)
    'e': 'ε',  # epsilon (visual)
    'i': 'ι',  # iota (visual)
    'o': 'ο',  # omicron (visual)
    'p': 'ρ',  # rho (visual - but also keyboard for π)
    'u': 'θ',  # theta (keyboard)
    'x': 'χ',  # chi (visual + keyboard)
    'y': 'υ',  # upsilon (visual + keyboard)
    # Lowercase - keyboard layout (Greek keyboard position)
    'b': 'β',  # beta (keyboard)
    'c': 'ψ',  # psi (keyboard)
    'd': 'δ',  # delta (keyboard)
    'f': 'φ',  # phi (keyboard)
    'g': 'γ',  # gamma (keyboard)
    'h': 'η',  # eta (keyboard)
    'j': 'ξ',  # xi (keyboard)
    'k': 'κ',  # kappa (keyboard)
    'l': 'λ',  # lambda (keyboard)
    'm': 'μ',  # mu (keyboard)
    'n': 'ν',  # nu (keyboard)
    'q': ';',  # not a letter on Greek keyboard
    'r': 'ρ',  # rho (keyboard)
    's': 'σ',  # sigma (keyboard)
    't': 'τ',  # tau (keyboard)
    'v': 'ω',  # omega (keyboard)
    'w': 'ς',  # final sigma (keyboard)
    'z': 'ζ',  # zeta (keyboard)
}

# Set of all Latin characters to detect
LATIN_CHARS = set(LATIN_TO_GREEK.keys())

# Build a character class string for regex
LATIN_CHARS_PATTERN = ''.join(re.escape(c) for c in LATIN_CHARS)


def extract_mixed_words(line):
    """Extract words that contain both Latin confusables and Greek characters.

    The standard extract_greek_words function only matches pure Greek characters,
    so mixed words like "Kύριος" (Latin K + Greek ύριος) get split.

    This function finds words containing BOTH Latin confusable characters AND
    Greek characters - these are the OCR errors we're looking for.

    Args:
        line: A line of text to scan

    Returns:
        List of words containing Latin characters mixed with Greek.
    """
    # Remove LaTeX commands first
    clean_line = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', ' ', line)
    clean_line = re.sub(r'\\[a-zA-Z]+', ' ', clean_line)

    # Pattern matches sequences that contain:
    # - Latin confusable characters (from our set)
    # - Greek characters (basic: \u0370-\u03FF, extended: \u1F00-\u1FFF)
    # We want words that have BOTH Latin and Greek mixed together
    mixed_pattern = rf'[{LATIN_CHARS_PATTERN}\u0370-\u03FF\u1F00-\u1FFF]+'

    candidates = re.findall(mixed_pattern, clean_line)

    # Filter to only keep words that have BOTH Latin confusables AND Greek chars
    mixed_words = []
    for word in candidates:
        has_latin = any(c in LATIN_CHARS for c in word)
        has_greek = any('\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF'
                        for c in word)
        if has_latin and has_greek:
            mixed_words.append(normalize_text(word))

    return mixed_words


def find_latin_characters(word):
    """Find all Latin characters in a word.

    Args:
        word: A word to check for Latin characters

    Returns:
        List of (position, latin_char) tuples for each Latin character found.
    """
    found = []
    for i, char in enumerate(word):
        if char in LATIN_CHARS:
            found.append((i, char))
    return found


def generate_suggested_fix(word):
    """Generate a suggested fix by replacing Latin chars with Greek equivalents.

    Args:
        word: Word containing Latin characters

    Returns:
        Word with Latin characters replaced by their Greek equivalents.
    """
    result = []
    for char in word:
        if char in LATIN_TO_GREEK:
            result.append(LATIN_TO_GREEK[char])
        else:
            result.append(char)
    return ''.join(result)


def process_brenton_file(brenton_path):
    """Process Brenton.tex and find Latin characters in Greek words.

    Args:
        brenton_path: Path to Brenton.tex file

    Returns:
        List of error dicts with source_file, verse_ref, line_num, word, etc.
    """
    errors = []
    parser = BrentonParser(brenton_path)
    source_file = Path(brenton_path).name

    for ctx in parser.parse():
        if not ctx.has_complete_ref:
            continue

        # Use our custom extraction that catches mixed Latin-Greek words
        # The standard greek_words extraction misses these because Latin
        # characters break the Greek-only regex pattern
        mixed_words = extract_mixed_words(ctx.line)

        for word in mixed_words:
            latin_chars = find_latin_characters(word)
            if latin_chars:
                # Format errors found as comma-separated list
                errors_found = ', '.join(char for _, char in latin_chars)
                errors.append({
                    'source_file': source_file,
                    'line_num': ctx.line_num,
                    'verse_ref': ctx.verse_ref,
                    'word': word,
                    'suggested_fix': generate_suggested_fix(word),
                    'errors_found': errors_found,
                    'full_line': ctx.line
                })

    return errors


def process_corrections_file(corrections_path):
    """Process word_corrections.tsv and find Latin characters in corrections.

    Args:
        corrections_path: Path to word_corrections.tsv file

    Returns:
        List of error dicts with source_file, verse_ref, line_num, word, etc.
    """
    errors = []
    source_file = Path(corrections_path).name

    print(f"Processing {corrections_path}...")

    try:
        with open(corrections_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            for line_num, row in enumerate(reader, 1):
                if len(row) < 3:
                    continue

                verse_ref = row[0]
                original_word = row[1]
                corrected_word = row[2]
                full_line = '\t'.join(row)

                # Check both original and corrected words for Latin characters
                for word, column in [(original_word, 'original'), (corrected_word, 'corrected')]:
                    mixed_words = extract_mixed_words(word)
                    for mixed_word in mixed_words:
                        latin_chars = find_latin_characters(mixed_word)
                        if latin_chars:
                            errors_found = ', '.join(char for _, char in latin_chars)
                            errors.append({
                                'source_file': source_file,
                                'line_num': line_num,
                                'verse_ref': f"{verse_ref} ({column})",
                                'word': mixed_word,
                                'suggested_fix': generate_suggested_fix(mixed_word),
                                'errors_found': errors_found,
                                'full_line': full_line
                            })
    except FileNotFoundError:
        print(f"Note: Corrections file '{corrections_path}' not found. Skipping.")

    return errors


def write_errors_tsv(errors, output_path):
    """Write detected errors to TSV file."""
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow([
            'Source File', 'Line Number', 'Verse Reference', 'Word',
            'Suggested Fix', 'Errors Found', 'Full Line'
        ])
        for error in errors:
            writer.writerow([
                error['source_file'],
                error['line_num'],
                error['verse_ref'],
                error['word'],
                error['suggested_fix'],
                error['errors_found'],
                error['full_line']
            ])
    print(f"Wrote {len(errors)} errors to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Detect Latin characters in Greek words in Brenton Septuagint'
    )
    parser.add_argument(
        '--input',
        default='../input/Brenton-corrected.tex',
        help='Path to input .tex source file (default: ../input/Brenton-corrected.tex)'
    )
    parser.add_argument(
        '--corrections',
        default='../word_corrections.tsv',
        help='Path to word corrections file (default: ../word_corrections.tsv)'
    )
    parser.add_argument(
        '--output',
        default='output/latin_characters.tsv',
        help='Output TSV file path (default: output/latin_characters.tsv)'
    )

    args = parser.parse_args()

    # Process both files
    errors = []
    errors.extend(process_brenton_file(args.input))
    errors.extend(process_corrections_file(args.corrections))

    # Write output
    write_errors_tsv(errors, args.output)

    # Print summary
    print(f"\nSummary:")
    print(f"  Total Latin characters in Greek words found: {len(errors)}")

    # Show breakdown by source file
    if errors:
        file_counts = {}
        for error in errors:
            file_counts[error['source_file']] = file_counts.get(error['source_file'], 0) + 1
        print(f"\n  Breakdown by source file:")
        for source, count in sorted(file_counts.items()):
            print(f"    {source}: {count}")

        # Show breakdown by character
        char_counts = {}
        for error in errors:
            for char in error['errors_found'].split(', '):
                char_counts[char] = char_counts.get(char, 0) + 1
        print(f"\n  Breakdown by character:")
        for char, count in sorted(char_counts.items(), key=lambda x: -x[1]):
            greek = LATIN_TO_GREEK.get(char, '?')
            print(f"    Latin '{char}' (should be Greek '{greek}'): {count}")


if __name__ == '__main__':
    main()
