#!/usr/bin/env python3
"""
Detect problematic unaccented words in Brenton Septuagint.

Detection logic:
- Single unaccented word: Flag if NOT a known enclitic/proclitic
- Two consecutive unaccented: Flag if at least one is NOT enclitic/proclitic
- Three+ consecutive unaccented: Always flag (suspicious even for enclitics)

Two consecutive valid enclitics are written to a separate file for manual review.
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.greek_utils import extract_accent_info, strip_diacritics
from shared.brenton_parser import BrentonParser


def load_enclitics_proclitics(filepath):
    """Load set of known enclitics and proclitics.

    Returns set of lowercase, diacritic-stripped forms for comparison.
    """
    valid_unaccented = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Store stripped form for comparison
            valid_unaccented.add(strip_diacritics(line).lower())
    return valid_unaccented


def word_has_accent(word):
    """Check if word has at least one accent."""
    return len(extract_accent_info(word)) > 0


def is_all_caps(word):
    """Check if word is all uppercase (headings/titles don't have accents)."""
    # Strip diacritics and check if all letters are uppercase
    stripped = strip_diacritics(word)
    # Only check actual letters, ignore punctuation
    letters = [c for c in stripped if c.isalpha()]
    return len(letters) > 0 and all(c.isupper() for c in letters)


def is_valid_unaccented(word, valid_set):
    """Check if word is a known enclitic/proclitic or all-caps (heading)."""
    # All-caps words (headings/titles) legitimately lack accents
    if is_all_caps(word):
        return True
    stripped = strip_diacritics(word).lower()
    return stripped in valid_set


def classify_sequence(sequence, valid_unaccented):
    """Classify an unaccented sequence.

    Returns dict with:
        - category: 'error', 'enclitic_pair', or 'ok'
        - reason: explanation string
    """
    length = len(sequence)

    # Skip if ALL words in sequence are all-caps (headings/titles)
    if all(is_all_caps(w) for w in sequence):
        return {'category': 'ok', 'reason': ''}

    # Rule 3: Always flag 3+ consecutive unaccented words
    if length >= 3:
        return {'category': 'error', 'reason': '3+ consecutive unaccented'}

    # Check which words are NOT valid enclitics/proclitics
    invalid_words = [w for w in sequence if not is_valid_unaccented(w, valid_unaccented)]

    if length == 1:
        # Rule 1: Single word - flag if not enclitic/proclitic
        if invalid_words:
            return {'category': 'error', 'reason': 'unknown unaccented word'}
        return {'category': 'ok', 'reason': ''}

    elif length == 2:
        # Rule 2: Two words - flag if at least one is not enclitic/proclitic
        if invalid_words:
            return {'category': 'error', 'reason': f'non-enclitic in pair: {", ".join(invalid_words)}'}
        else:
            # Both are valid enclitics - put in secondary list for review
            return {'category': 'enclitic_pair', 'reason': 'consecutive enclitics'}

    return {'category': 'ok', 'reason': ''}


def process_brenton_file(brenton_path, valid_unaccented):
    """Process Brenton.tex and find problematic unaccented sequences.

    Returns:
        Tuple of (errors, enclitic_pairs) where:
        - errors: List of definite issues to fix
        - enclitic_pairs: List of consecutive enclitic pairs for manual review
    """
    errors = []
    enclitic_pairs = []
    parser = BrentonParser(brenton_path)
    last_book = None

    for ctx in parser.parse():
        if ctx.book and ctx.book != last_book:
            print(f"Processing book: {ctx.book}")
            last_book = ctx.book

        if not ctx.has_complete_ref or not ctx.greek_words:
            continue

        # Track sequences of unaccented words
        unaccented_sequence = []
        prev_accented = None

        for word in ctx.greek_words:
            # Skip all-caps words entirely (headings/titles) - they don't participate in sequences
            if is_all_caps(word):
                continue

            if word_has_accent(word):
                # Sequence ends - apply detection logic
                if unaccented_sequence:
                    result = classify_sequence(unaccented_sequence, valid_unaccented)
                    entry = {
                        'line_num': ctx.line_num,
                        'verse_ref': ctx.verse_ref,
                        'unaccented_words': ' '.join(unaccented_sequence),
                        'sequence_length': len(unaccented_sequence),
                        'reason': result['reason'],
                        'context_before': prev_accented or '',
                        'context_after': word,
                        'full_line': ctx.line
                    }
                    if result['category'] == 'error':
                        errors.append(entry)
                    elif result['category'] == 'enclitic_pair':
                        enclitic_pairs.append(entry)
                # Reset sequence
                unaccented_sequence = []
                prev_accented = word
            else:
                unaccented_sequence.append(word)

        # Check sequence at end of verse
        if unaccented_sequence:
            result = classify_sequence(unaccented_sequence, valid_unaccented)
            entry = {
                'line_num': ctx.line_num,
                'verse_ref': ctx.verse_ref,
                'unaccented_words': ' '.join(unaccented_sequence),
                'sequence_length': len(unaccented_sequence),
                'reason': result['reason'],
                'context_before': prev_accented or '',
                'context_after': '',
                'full_line': ctx.line
            }
            if result['category'] == 'error':
                errors.append(entry)
            elif result['category'] == 'enclitic_pair':
                enclitic_pairs.append(entry)

    return errors, enclitic_pairs


def write_errors_tsv(errors, output_path):
    """Write detected errors to TSV file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow([
            'Line Number',
            'Verse Reference',
            'Unaccented Words',
            'Sequence Length',
            'Reason',
            'Context Before',
            'Context After',
            'Full Line'
        ])
        for error in errors:
            writer.writerow([
                error['line_num'],
                error['verse_ref'],
                error['unaccented_words'],
                error['sequence_length'],
                error['reason'],
                error['context_before'],
                error['context_after'],
                error['full_line']
            ])


def main():
    parser = argparse.ArgumentParser(
        description='Detect problematic unaccented words in Brenton Septuagint'
    )
    parser.add_argument(
        '--input',
        default='../input/Brenton.tex',
        help='Path to input .tex file (default: ../input/Brenton.tex)'
    )
    parser.add_argument(
        '--enclitics',
        default='../input/enclitics_proclitics.txt',
        help='Path to enclitics/proclitics list (default: ../input/enclitics_proclitics.txt)'
    )
    parser.add_argument(
        '--output',
        default='output/unaccented_sequences.tsv',
        help='Output TSV file path (default: output/unaccented_sequences.tsv)'
    )
    parser.add_argument(
        '--enclitic-pairs-output',
        default='output/consecutive_enclitics.tsv',
        help='Output TSV for consecutive enclitic pairs (default: output/consecutive_enclitics.tsv)'
    )

    args = parser.parse_args()

    print(f"Loading enclitics/proclitics from {args.enclitics}...")
    valid_unaccented = load_enclitics_proclitics(args.enclitics)
    print(f"  Loaded {len(valid_unaccented)} valid unaccented forms")

    print(f"Detecting problematic unaccented words in {args.input}...")
    errors, enclitic_pairs = process_brenton_file(args.input, valid_unaccented)

    print(f"\nWriting main results to {args.output}...")
    write_errors_tsv(errors, args.output)

    print(f"Writing enclitic pairs to {args.enclitic_pairs_output}...")
    write_errors_tsv(enclitic_pairs, args.enclitic_pairs_output)

    print(f"\nSummary:")
    print(f"  Definite issues: {len(errors)}")
    print(f"  Enclitic pairs (for review): {len(enclitic_pairs)}")

    # Count errors by reason
    by_reason = {}
    for error in errors:
        reason = error['reason']
        by_reason[reason] = by_reason.get(reason, 0) + 1

    if by_reason:
        print(f"\n  Issues by type:")
        for reason in sorted(by_reason.keys()):
            print(f"    {reason}: {by_reason[reason]}")


if __name__ == '__main__':
    main()
