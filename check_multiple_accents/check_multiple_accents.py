#!/usr/bin/env python3
"""
Detect words with multiple accents in Brenton Septuagint.

Identifies potential OCR merge errors where two words were combined
but both retained their accents. Filters out valid enclisis cases
by checking if the following word still has an accent.

Detection logic:
- If a word has 3+ accents: Always flag (impossible in Greek)
- If a word has exactly 2 accents: Flag unless the following word
  has no accent (which would indicate valid enclisis)
"""

import csv
import argparse
import sys
from pathlib import Path

# Add parent directory to path to import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.greek_utils import extract_accent_info
from shared.brenton_parser import BrentonParser


def get_accents(word):
    """Get accent information for a word.

    Returns:
        List of (position, accent_type, base_char) tuples.
        Empty list if word has no accents.
    """
    return extract_accent_info(word)


def word_has_accent(word):
    """Check if a word has at least one accent.

    Returns:
        True if word has one or more accents, False otherwise.
    """
    return len(extract_accent_info(word)) > 0


def format_accent_info(accents):
    """Format accent information for output.

    Args:
        accents: List of (position, accent_type, base_char) tuples

    Returns:
        String like "pos 3: GRAVE on ι, pos 7: ACUTE on ο"
    """
    parts = []
    for pos, accent_type, base_char in accents:
        parts.append(f"pos {pos}: {accent_type} on {base_char}")
    return "; ".join(parts)


def process_brenton_file(brenton_path):
    """Process Brenton.tex and find words with multiple accents.

    Returns:
        List of error dicts with verse_ref, line_num, word, accents, etc.
    """
    errors = []
    parser = BrentonParser(brenton_path)
    last_book = None

    for ctx in parser.parse():
        # Print book progress
        if ctx.book and ctx.book != last_book:
            print(f"Processing book: {ctx.book}")
            last_book = ctx.book

        if not ctx.has_complete_ref or not ctx.greek_words:
            continue

        # Check each word in the verse
        for i, word in enumerate(ctx.greek_words):
            accents = get_accents(word)
            accent_count = len(accents)

            if accent_count < 2:
                continue

            # Determine if we should flag this word
            should_flag = False
            following_word = None
            following_has_accent = None

            if accent_count >= 3:
                # Always flag 3+ accents (impossible in Greek)
                should_flag = True
                if i + 1 < len(ctx.greek_words):
                    following_word = ctx.greek_words[i + 1]
                    following_has_accent = word_has_accent(following_word)
            else:
                # Exactly 2 accents - check for enclisis
                if i + 1 < len(ctx.greek_words):
                    following_word = ctx.greek_words[i + 1]
                    following_has_accent = word_has_accent(following_word)
                    # Flag if following word has accent (not enclisis)
                    if following_has_accent:
                        should_flag = True
                else:
                    # No following word - always flag
                    should_flag = True

            if should_flag:
                # Format following word accent status
                if following_word is None:
                    following_accent_status = "N/A"
                elif following_has_accent:
                    following_accent_status = "Yes"
                else:
                    following_accent_status = "No"

                errors.append({
                    'line_num': ctx.line_num,
                    'verse_ref': ctx.verse_ref,
                    'word': word,
                    'accent_count': accent_count,
                    'accent_positions': format_accent_info(accents),
                    'following_word': following_word if following_word else "",
                    'following_has_accent': following_accent_status,
                    'full_line': ctx.line
                })

    return errors


def write_errors_tsv(errors, output_path):
    """Write detected errors to TSV file."""
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        # Write header
        writer.writerow([
            'Line Number',
            'Verse Reference',
            'Word',
            'Following Word',
            'Following Word Has Accent',
            'Accent Count',
            'Accent Positions',
            'Full Line'
        ])

        # Write data
        for error in errors:
            writer.writerow([
                error['line_num'],
                error['verse_ref'],
                error['word'],
                error['following_word'],
                error['following_has_accent'],
                error['accent_count'],
                error['accent_positions'],
                error['full_line']
            ])


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Detect words with multiple accents in Brenton Septuagint.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default paths:
  python check_multiple_accents.py

  # Specify custom input file:
  python check_multiple_accents.py --input /path/to/MyText.tex
        """
    )

    parser.add_argument('--input', default='../input/Brenton.tex',
                        help='Path to input .tex file (default: ../input/Brenton.tex)')
    parser.add_argument('--output', default='output/multiple_accents.tsv',
                        help='Path to output TSV file (default: output/multiple_accents.tsv)')

    args = parser.parse_args()

    print(f"Detecting words with multiple accents in {args.input}...")
    errors = process_brenton_file(args.input)

    print(f"\nWriting results to {args.output}...")
    write_errors_tsv(errors, args.output)

    # Print summary
    print(f"\nSummary:")
    print(f"  Total words with multiple accents found: {len(errors)}")

    # Count by accent count
    by_count = {}
    for error in errors:
        count = error['accent_count']
        by_count[count] = by_count.get(count, 0) + 1

    for count in sorted(by_count.keys()):
        print(f"    {count} accents: {by_count[count]}")

    print(f"\nResults saved to: {args.output}")


if __name__ == '__main__':
    main()
