#!/usr/bin/env python3
"""
Detect OCR sequence errors in Brenton Septuagint by word-by-word alignment
against Rahlfs edition, focusing on character substitutions and sequence confusions.

Detects:
- Single-char confusions: υ/ν/ς/σ (within group), ο/ω (within group, disabled)
- Sequence confusions: ην↔ης, οι↔αι

This script complements check_missing_words_for_typos by catching errors that
pass vocabulary checks but are wrong in context (e.g., both -ου and -ον endings
can be valid Greek, but only one is correct for a given word form).
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher

# Add parent directory to path to import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.greek_utils import (
    normalize_text,
    strip_diacritics,
    extract_greek_words,
    load_accepted_words,
    load_already_examined,
    should_filter_by_accent
)
from shared.data_loaders import (
    load_words_with_ids,
    load_versification,
    get_verse_words
)
from shared.book_code_mappings import convert_brenton_reference_to_rahlfs

# Groups of characters that can be OCR-confused with each other.
# Characters are only considered confusable within the same group.
CONFUSABLE_CHAR_GROUPS = [
    {'υ', 'ν', 'ς', 'σ'},  # visual similarity in many typefaces
    # {'ο', 'ω'},            # omicron/omega (e.g., indicative vs subjunctive)
]

# Multi-character sequences that can be OCR-confused
CONFUSABLE_SEQUENCES = [
    ('ην', 'ης'),  # e.g., -ην/-ης endings
    ('οι', 'αι'),  # e.g., dative plural endings -οις/-αις
]


def get_verse_word_list(verse_ref, verse_map, sorted_verses, words_dict):
    """Get ordered list of words for a verse (not just a dict).

    Returns list of tuples: [(normalized, original), ...]
    """
    if verse_ref not in verse_map:
        return []

    start_id = verse_map[verse_ref]

    # Find the next verse to get end boundary
    current_idx = None
    for i, (v_ref, v_id) in enumerate(sorted_verses):
        if v_ref == verse_ref:
            current_idx = i
            break

    if current_idx is None:
        return []

    # Determine end ID
    if current_idx + 1 < len(sorted_verses):
        end_id = sorted_verses[current_idx + 1][1] - 1
    else:
        end_id = max(words_dict.keys()) if words_dict else start_id

    # Extract words in order
    words_list = []
    for word_id in range(start_id, end_id + 1):
        if word_id in words_dict:
            word_data = words_dict[word_id]
            words_list.append((word_data['normalized'], word_data['original']))

    return words_list


def align_word_sequences(brenton_words, rahlfs_words):
    """Align two word sequences using SequenceMatcher.

    Args:
        brenton_words: List of (normalized, original) tuples from Brenton
        rahlfs_words: List of (normalized, original) tuples from Rahlfs

    Returns:
        List of alignment tuples:
        - ('equal', brenton_idx, rahlfs_idx) - words match
        - ('replace', brenton_idx, rahlfs_idx) - different words at aligned positions
        - ('insert', None, rahlfs_idx) - word in Rahlfs but not Brenton
        - ('delete', brenton_idx, None) - word in Brenton but not Rahlfs
    """
    # Extract just normalized forms for alignment
    b_normalized = [w[0] for w in brenton_words]
    r_normalized = [w[0] for w in rahlfs_words]

    matcher = SequenceMatcher(None, b_normalized, r_normalized)
    alignments = []

    for op, b_start, b_end, r_start, r_end in matcher.get_opcodes():
        if op == 'equal':
            for i, j in zip(range(b_start, b_end), range(r_start, r_end)):
                alignments.append(('equal', i, j))
        elif op == 'replace':
            # Pair up replacements as much as possible
            b_range = list(range(b_start, b_end))
            r_range = list(range(r_start, r_end))
            for i, (bi, ri) in enumerate(zip(b_range, r_range)):
                alignments.append(('replace', bi, ri))
            # Handle remaining unpaired items
            if len(b_range) > len(r_range):
                for bi in b_range[len(r_range):]:
                    alignments.append(('delete', bi, None))
            elif len(r_range) > len(b_range):
                for ri in r_range[len(b_range):]:
                    alignments.append(('insert', None, ri))
        elif op == 'delete':
            for bi in range(b_start, b_end):
                alignments.append(('delete', bi, None))
        elif op == 'insert':
            for ri in range(r_start, r_end):
                alignments.append(('insert', None, ri))

    return alignments


def detect_single_char_confusion(brenton_word, rahlfs_word):
    """Detect single-character confusions (υ/ν/ς/σ).

    Returns dict with detection info if found, None otherwise.
    """
    b_norm = strip_diacritics(brenton_word.lower())
    r_norm = strip_diacritics(rahlfs_word.lower())

    if len(b_norm) != len(r_norm):
        return None

    if b_norm == r_norm:
        return None

    diffs = []
    for i, (b_char, r_char) in enumerate(zip(b_norm, r_norm)):
        if b_char != r_char:
            diffs.append((i, b_char, r_char))

    if not diffs:
        return None

    # All differences must be within the same confusable character group
    for _, b_char, r_char in diffs:
        found_in_same_group = False
        for group in CONFUSABLE_CHAR_GROUPS:
            if b_char in group and r_char in group:
                found_in_same_group = True
                break
        if not found_in_same_group:
            return None

    # Determine context (ending pattern)
    context = ""
    if diffs:
        last_diff_pos = diffs[-1][0]
        if last_diff_pos >= len(b_norm) - 3:
            # Difference is near the end - show ending
            context = f"-{b_norm[max(0, last_diff_pos-1):]} → -{r_norm[max(0, last_diff_pos-1):]}"

    return {
        'type': 'single_char',
        'positions': diffs,
        'brenton_normalized': b_norm,
        'rahlfs_normalized': r_norm,
        'context': context
    }


def detect_sequence_confusion(brenton_word, rahlfs_word):
    """Detect multi-character sequence confusions (ην/ης, οι/αι).

    Returns dict with detection info if found, None otherwise.
    """
    b_norm = strip_diacritics(brenton_word.lower())
    r_norm = strip_diacritics(rahlfs_word.lower())

    if b_norm == r_norm:
        return None

    # Try each confusable sequence pair
    for seq1, seq2 in CONFUSABLE_SEQUENCES:
        # Try replacing seq1 with seq2 in brenton, see if it matches rahlfs
        if seq1 in b_norm:
            if b_norm.replace(seq1, seq2) == r_norm:
                return {
                    'type': 'sequence',
                    'from_seq': seq1,
                    'to_seq': seq2,
                    'brenton_normalized': b_norm,
                    'rahlfs_normalized': r_norm,
                    'context': f"{seq1} → {seq2}"
                }
        # Try reverse direction
        if seq2 in b_norm:
            if b_norm.replace(seq2, seq1) == r_norm:
                return {
                    'type': 'sequence',
                    'from_seq': seq2,
                    'to_seq': seq1,
                    'brenton_normalized': b_norm,
                    'rahlfs_normalized': r_norm,
                    'context': f"{seq2} → {seq1}"
                }

    return None


def should_skip_word(word, verse_ref, accepted_words, corrections):
    """Check if word should be skipped (already in accepted list or corrections)."""
    normalized = strip_diacritics(word.lower())

    # Check accepted words
    if normalized in accepted_words:
        return True

    # Check corrections file (column 2 = original incorrect word)
    if (verse_ref, normalized) in corrections:
        return True

    # Also check ALL corrections
    if ('ALL', normalized) in corrections:
        return True

    return False


def load_accepted_sequence_variants(filepath):
    """Load accepted sequence variants from TSV file.

    Returns set of (verse_ref, brenton_word_normalized, rahlfs_word_normalized) tuples.
    """
    print(f"Opening accepted sequence variants file: {filepath}")
    accepted = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            row_count = 0
            for row in reader:
                row_count += 1
                # Skip comments and empty lines
                if not row or row[0].startswith('#'):
                    continue
                if len(row) >= 3:
                    verse_ref = normalize_text(row[0].strip())
                    brenton_word = normalize_text(row[1].strip())
                    rahlfs_word = normalize_text(row[2].strip())
                    # Normalize for comparison
                    b_normalized = strip_diacritics(brenton_word.lower())
                    r_normalized = strip_diacritics(rahlfs_word.lower())
                    accepted.add((verse_ref, b_normalized, r_normalized))
            print(f"Finished reading {filepath} ({row_count} lines, {len(accepted)} variants loaded)")
    except FileNotFoundError:
        print(f"Note: Accepted sequence variants file '{filepath}' not found. Continuing without it.")
    except Exception as e:
        print(f"Error loading accepted sequence variants from {filepath}: {e}")
    return accepted


def is_accepted_variant(verse_ref, brenton_word, rahlfs_word, accepted_variants):
    """Check if this specific verse+word pair is an accepted variant."""
    b_normalized = strip_diacritics(brenton_word.lower())
    r_normalized = strip_diacritics(rahlfs_word.lower())
    return (verse_ref, b_normalized, r_normalized) in accepted_variants


def process_brenton_file(brenton_path, rahlfs_words_dict, rahlfs_verse_map,
                         rahlfs_sorted_verses, accepted_words, corrections,
                         accepted_variants):
    """Process Brenton.tex and find sequence errors.

    Returns:
        (errors, mismatches) where:
        - errors: list of detected confusion errors
        - mismatches: list of versification mismatches
    """
    errors = []
    mismatches = []

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

            # Extract words from this line
            brenton_words_raw = extract_greek_words(line)
            if not brenton_words_raw:
                continue

            # Convert to (normalized, original) tuples
            brenton_words = [(strip_diacritics(w.lower()), w) for w in brenton_words_raw]

            # Get Rahlfs reference
            rahlfs_ref = convert_brenton_reference_to_rahlfs(
                current_book, current_chapter, current_verse
            )

            if rahlfs_ref is None:
                mismatches.append({
                    'brenton_ref': f"{current_book} {current_chapter}:{current_verse}",
                    'rahlfs_ref': None,
                    'status': 'conversion_failed',
                    'line_num': line_num
                })
                continue

            # Get Rahlfs words for this verse
            rahlfs_words = get_verse_word_list(
                rahlfs_ref, rahlfs_verse_map, rahlfs_sorted_verses, rahlfs_words_dict
            )

            if not rahlfs_words:
                mismatches.append({
                    'brenton_ref': f"{current_book} {current_chapter}:{current_verse}",
                    'rahlfs_ref': rahlfs_ref,
                    'status': 'not_found',
                    'line_num': line_num
                })
                continue

            # Align word sequences
            alignments = align_word_sequences(brenton_words, rahlfs_words)

            # Check each aligned pair for confusions
            verse_ref = f"{current_book} {current_chapter}:{current_verse}"

            for op, b_idx, r_idx in alignments:
                if op != 'replace':
                    continue  # Only check replacements (different words at same position)

                b_word = brenton_words[b_idx]
                r_word = rahlfs_words[r_idx]

                # Skip if word is in accepted list or corrections
                if should_skip_word(b_word[1], verse_ref, accepted_words, corrections):
                    continue

                # Skip if this specific variant is accepted
                if is_accepted_variant(verse_ref, b_word[1], r_word[1], accepted_variants):
                    continue

                # Check for single-char confusion
                confusion = detect_single_char_confusion(b_word[1], r_word[1])
                if confusion:
                    # Skip if accent differences indicate valid variant
                    if should_filter_by_accent(b_word[1], r_word[1]):
                        continue
                    errors.append({
                        'verse_ref': verse_ref,
                        'line_num': line_num,
                        'brenton_word': b_word[1],
                        'rahlfs_word': r_word[1],
                        'error_type': confusion['type'],
                        'context': confusion['context'],
                        'full_line': line.strip()
                    })
                    continue

                # Check for sequence confusion
                confusion = detect_sequence_confusion(b_word[1], r_word[1])
                if confusion:
                    # Skip if accent differences indicate valid variant
                    if should_filter_by_accent(b_word[1], r_word[1]):
                        continue
                    errors.append({
                        'verse_ref': verse_ref,
                        'line_num': line_num,
                        'brenton_word': b_word[1],
                        'rahlfs_word': r_word[1],
                        'error_type': confusion['type'],
                        'context': confusion['context'],
                        'full_line': line.strip()
                    })

    return errors, mismatches


def write_errors_tsv(errors, output_path):
    """Write detected errors to TSV file."""
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow([
            'Verse Reference', 'Line Number', 'Brenton Word', 'Rahlfs Word',
            'Error Type', 'Context', 'Full Line'
        ])
        for error in errors:
            writer.writerow([
                error['verse_ref'],
                error['line_num'],
                error['brenton_word'],
                error['rahlfs_word'],
                error['error_type'],
                error['context'],
                error['full_line']
            ])
    print(f"Wrote {len(errors)} errors to {output_path}")


def write_mismatches_tsv(mismatches, output_path):
    """Write versification mismatches to TSV file."""
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow([
            'Brenton Reference', 'Rahlfs Reference', 'Status', 'Line Number'
        ])
        for mismatch in mismatches:
            writer.writerow([
                mismatch['brenton_ref'],
                mismatch['rahlfs_ref'] or 'N/A',
                mismatch['status'],
                mismatch['line_num']
            ])
    print(f"Wrote {len(mismatches)} mismatches to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Detect OCR sequence errors (υ/ν/ς confusion) in Brenton LXX'
    )
    parser.add_argument(
        '--brenton',
        default='../check_missing_words_for_typos/input/Brenton.tex',
        help='Path to Brenton.tex file'
    )
    parser.add_argument(
        '--rahlfs-words',
        default='../check_missing_words_for_typos/input/rahlfs_words.csv',
        help='Path to Rahlfs words CSV'
    )
    parser.add_argument(
        '--rahlfs-versification',
        default='../check_missing_words_for_typos/input/rahlfs_versification.csv',
        help='Path to Rahlfs versification CSV'
    )
    parser.add_argument(
        '--accepted-words',
        default='../accepted_words.txt',
        help='Path to accepted words file'
    )
    parser.add_argument(
        '--corrections',
        default='../word_corrections.tsv',
        help='Path to word corrections file'
    )
    parser.add_argument(
        '--output',
        default='output/sequence_errors.tsv',
        help='Path to output TSV file'
    )
    parser.add_argument(
        '--mismatches-output',
        default='output/versification_mismatches.tsv',
        help='Path to versification mismatches output'
    )
    parser.add_argument(
        '--accepted-variants',
        default='../accepted_sequence_variants.tsv',
        help='Path to accepted sequence variants file'
    )

    args = parser.parse_args()

    # Load reference data
    print("Loading Rahlfs words...")
    rahlfs_words_dict = load_words_with_ids(args.rahlfs_words)

    print("Loading Rahlfs versification...")
    rahlfs_verse_map, rahlfs_sorted_verses = load_versification(args.rahlfs_versification)

    print("Loading accepted words...")
    accepted_words = load_accepted_words(args.accepted_words)

    print("Loading corrections...")
    corrections = load_already_examined(args.corrections)

    print("Loading accepted sequence variants...")
    accepted_variants = load_accepted_sequence_variants(args.accepted_variants)

    # Process Brenton file
    errors, mismatches = process_brenton_file(
        args.brenton,
        rahlfs_words_dict,
        rahlfs_verse_map,
        rahlfs_sorted_verses,
        accepted_words,
        corrections,
        accepted_variants
    )

    # Write outputs
    write_errors_tsv(errors, args.output)
    write_mismatches_tsv(mismatches, args.mismatches_output)

    # Summary
    print(f"\nSummary:")
    print(f"  Total errors found: {len(errors)}")
    print(f"  - Single char (υ/ν/ς/σ, ο/ω): {sum(1 for e in errors if e['error_type'] == 'single_char')}")
    print(f"  - Sequence (ην/ης, οι/αι): {sum(1 for e in errors if e['error_type'] == 'sequence')}")
    print(f"  Versification mismatches: {len(mismatches)}")


if __name__ == '__main__':
    main()
