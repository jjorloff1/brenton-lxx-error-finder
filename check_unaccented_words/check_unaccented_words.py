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
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.greek_utils import extract_accent_info, strip_diacritics, normalize_text
from shared.brenton_parser import BrentonParser
from shared.data_loaders import load_words_with_ids, derive_word_set

# Punctuation that breaks sequences (elision marks, apostrophes, etc.)
SEQUENCE_BREAKING_PUNCTUATION = set("'ʼʹ᾽᾿.,;·:!?()[]{}\"«»—–-")


def has_punctuation_after(word, line):
    """Check if a word is followed by punctuation in the original line.

    Returns True if punctuation immediately follows the word.
    """
    # Find the word in the line
    # Use a pattern that matches the word followed by optional punctuation
    pattern = re.escape(word) + r"(['\u02BC\u02B9\u1FBD\u1FBF.,;·:!?()\[\]{}\"«»—–-])"
    match = re.search(pattern, line)
    return match is not None


def get_breathing_mark(word):
    """Extract the breathing mark from a word's first vowel, if present.

    Returns the breathing mark character (U+0313 smooth or U+0314 rough),
    or None if no breathing mark found.
    """
    # Greek vowels that can carry breathing marks
    vowels = set('αεηιουωἀἁἂἃἄἅἆἇἐἑἒἓἔἕἠἡἢἣἤἥἦἧἰἱἲἳἴἵἶἷὀὁὂὃὄὅὐὑὒὓὔὕὖὗὠὡὢὣὤὥὦὧ'
                 'ΑΕΗΙΟΥΩἈἉἊἋἌἍἎἏἘἙἚἛἜἝἨἩἪἫἬἭἮἯἸἹἺἻἼἽἾἿὈὉὊὋὌὍὙὛὝὟὨὩὪὫὬὭὮὯ'
                 'ᾀᾁᾂᾃᾄᾅᾆᾇᾐᾑᾒᾓᾔᾕᾖᾗᾠᾡᾢᾣᾤᾥᾦᾧᾈᾉᾊᾋᾌᾍᾎᾏᾘᾙᾚᾛᾜᾝᾞᾟᾨᾩᾪᾫᾬᾭᾮᾯ')

    # Decompose the word to find combining characters
    nfd = unicodedata.normalize('NFD', normalize_text(word))

    for i, char in enumerate(nfd):
        base_lower = char.lower()
        # Check if this is a vowel (or first letter of word)
        if base_lower in 'αεηιουω' or char in vowels:
            # Look at following combining characters
            for j in range(i + 1, len(nfd)):
                c = nfd[j]
                cat = unicodedata.category(c)
                if cat != 'Mn':
                    break  # No more combining marks
                if ord(c) == 0x0313:  # Smooth breathing
                    return '\u0313'
                if ord(c) == 0x0314:  # Rough breathing
                    return '\u0314'
            return None  # First vowel has no breathing mark
    return None


def apply_breathing_mark(word, breathing_mark):
    """Apply a breathing mark to a word's first vowel if it doesn't have one.

    If the word already has a breathing mark, returns unchanged.
    """
    if not breathing_mark:
        return word

    # Check if word already has a breathing mark
    existing = get_breathing_mark(word)
    if existing:
        return word  # Already has one

    # Find the first vowel and add the breathing mark
    nfd = unicodedata.normalize('NFD', normalize_text(word))
    result = []
    applied = False

    for char in nfd:
        result.append(char)
        if not applied and char.lower() in 'αεηιουω':
            # Add breathing mark after the vowel (before other combining marks ideally)
            result.append(breathing_mark)
            applied = True

    return unicodedata.normalize('NFC', ''.join(result))


def get_ultima_accent_info(word):
    """Check if a word has an accent on the ultima (last syllable).

    Returns tuple of (has_ultima_accent, accent_type, accent_position_in_nfd)
    where accent_type is 'ACUTE', 'GRAVE', or 'CIRCUMFLEX'.
    Returns (False, None, None) if no accent on ultima.
    """
    vowels = set('αεηιουωἀἁἂἃἄἅἆἇἐἑἒἓἔἕἠἡἢἣἤἥἦἧἰἱἲἳἴἵἶἷὀὁὂὃὄὅὐὑὒὓὔὕὖὗὠὡὢὣὤὥὦὧ'
                 'ᾀᾁᾂᾃᾄᾅᾆᾇᾐᾑᾒᾓᾔᾕᾖᾗᾠᾡᾢᾣᾤᾥᾦᾧ')

    nfd = unicodedata.normalize('NFD', normalize_text(word))

    # Find all vowel positions
    vowel_positions = []
    for i, char in enumerate(nfd):
        if char.lower() in 'αεηιουω' or char in vowels:
            vowel_positions.append(i)

    if not vowel_positions:
        return (False, None, None)

    # Get the last vowel position
    last_vowel_pos = vowel_positions[-1]

    # Check if there's an accent after the last vowel
    for i in range(last_vowel_pos + 1, len(nfd)):
        char = nfd[i]
        cat = unicodedata.category(char)
        if cat != 'Mn':
            break  # Hit a non-combining character, stop
        code = ord(char)
        if code == 0x0301:  # Acute
            return (True, 'ACUTE', i)
        if code == 0x0300:  # Grave
            return (True, 'GRAVE', i)
        if code == 0x0342:  # Circumflex
            return (True, 'CIRCUMFLEX', i)

    return (False, None, None)


def convert_ultima_acute_to_grave(word):
    """Convert acute accent on ultima to grave accent.

    Only converts if the word has an acute on the last syllable.
    """
    has_ultima, accent_type, accent_pos = get_ultima_accent_info(word)

    if not has_ultima or accent_type != 'ACUTE':
        return word

    # Replace acute with grave
    nfd = unicodedata.normalize('NFD', normalize_text(word))
    nfd_list = list(nfd)
    nfd_list[accent_pos] = '\u0300'  # Replace acute with grave
    return unicodedata.normalize('NFC', ''.join(nfd_list))


def convert_ultima_grave_to_acute(word):
    """Convert grave accent on ultima to acute accent.

    Only converts if the word has a grave on the last syllable.
    """
    has_ultima, accent_type, accent_pos = get_ultima_accent_info(word)

    if not has_ultima or accent_type != 'GRAVE':
        return word

    # Replace grave with acute
    nfd = unicodedata.normalize('NFD', normalize_text(word))
    nfd_list = list(nfd)
    nfd_list[accent_pos] = '\u0301'  # Replace grave with acute
    return unicodedata.normalize('NFC', ''.join(nfd_list))


def is_at_sentence_end(word, line, is_end_of_verse):
    """Check if a word is at the end of a sentence.

    Sentence end indicators: · (ano teleia), . (period), or end of verse.
    """
    if is_end_of_verse:
        return True

    # Check if word is followed by sentence-ending punctuation
    # Look for the word followed by · or .
    pattern = re.escape(word) + r'\s*[·.]'
    return re.search(pattern, line) is not None


def count_accents(word):
    """Count the number of accents in a word."""
    nfd = unicodedata.normalize('NFD', normalize_text(word))
    count = 0
    for char in nfd:
        code = ord(char)
        if code in (0x0300, 0x0301, 0x0342):  # Grave, Acute, Circumflex
            count += 1
    return count


def remove_extra_accents(word):
    """Remove all but the first accent from a word.

    Some word lists have double accents (e.g., ἐποίησέ) which occur in specific
    grammatical contexts but shouldn't be our default suggestion.
    """
    if count_accents(word) <= 1:
        return word

    nfd = unicodedata.normalize('NFD', normalize_text(word))
    result = []
    found_accent = False

    for char in nfd:
        code = ord(char)
        if code in (0x0300, 0x0301, 0x0342):  # Grave, Acute, Circumflex
            if not found_accent:
                result.append(char)
                found_accent = True
            # Skip additional accents
        else:
            result.append(char)

    return unicodedata.normalize('NFC', ''.join(result))


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


def suggest_fix(word, valid_enclitics, rahlfs_words, swete_words):
    """Suggest the correctly accented version of a word.

    For enclitics/proclitics, returns empty string (they're valid without accents).
    For other words, looks up in Swete first (better for proper nouns), then Rahlfs.
    For capitalized words, prefers Swete (better diacritics on proper nouns).
    Preserves the original casing and breathing marks.

    Args:
        word: The unaccented word from the text
        valid_enclitics: Set of valid enclitic/proclitic forms
        rahlfs_words: Dict mapping normalized -> original from Rahlfs
        swete_words: Dict mapping normalized -> original from Swete

    Returns:
        Suggested accented form, or empty string if not found or enclitic
    """
    # Skip all-caps words (headings)
    if is_all_caps(word):
        return ''

    stripped = strip_diacritics(word).lower()

    # Enclitics/proclitics are valid without accents
    if stripped in valid_enclitics:
        return ''

    # For capitalized words (likely proper nouns), prefer Swete then Rahlfs
    # For lowercase words, also prefer Swete (it generally has better diacritics)
    suggestion = None
    if stripped in swete_words:
        suggestion = swete_words[stripped]
    elif stripped in rahlfs_words:
        suggestion = rahlfs_words[stripped]

    if suggestion:
        # Remove extra accents (some word lists have double-accented forms)
        suggestion = remove_extra_accents(suggestion)

        # Preserve initial capitalization if original had it
        if word and word[0].isupper() and suggestion and suggestion[0].islower():
            # Handle Greek iota subscript: when uppercased, ᾠ becomes ὨΙ (two chars)
            # Only capitalize if it doesn't add extra characters
            first_upper = suggestion[0].upper()
            if len(first_upper) == 1:
                suggestion = first_upper + suggestion[1:]
            # If uppercasing adds characters (iota adscript), leave lowercase
            # to avoid corrupting the word

        # Preserve breathing mark from original if suggestion lacks one
        original_breathing = get_breathing_mark(word)
        if original_breathing:
            suggestion = apply_breathing_mark(suggestion, original_breathing)

        return suggestion

    return ''


def suggest_fixes_for_sequence(words, valid_enclitics, rahlfs_words, swete_words,
                                line, is_last_in_verse):
    """Generate suggested fixes for a sequence of unaccented words.

    Handles ultima accent conversion:
    - Words at sentence end (before · or . or end of verse) keep acute on ultima
    - Words mid-sentence get grave on ultima

    Args:
        words: List of unaccented words
        valid_enclitics: Set of valid enclitic/proclitic forms
        rahlfs_words: Dict mapping normalized -> original from Rahlfs
        swete_words: Dict mapping normalized -> original from Swete
        line: The full line from the source file
        is_last_in_verse: True if this sequence is at end of verse

    Returns:
        Space-separated suggested fixes (original word if no fix found).
    """
    suggestions = []
    for i, word in enumerate(words):
        fix = suggest_fix(word, valid_enclitics, rahlfs_words, swete_words)
        if not fix:
            suggestions.append(word)  # Keep original if no fix found
            continue

        # Determine if this word is at sentence end
        is_last_word_in_sequence = (i == len(words) - 1)

        if is_last_word_in_sequence:
            # Last word in sequence - check if at sentence end
            at_sentence_end = is_at_sentence_end(word, line, is_last_in_verse)
        else:
            # Not last word in sequence - definitely mid-sentence
            at_sentence_end = False

        # Adjust ultima accent based on position
        if at_sentence_end:
            # At sentence end: acute on ultima
            fix = convert_ultima_grave_to_acute(fix)
        else:
            # Mid-sentence: grave on ultima
            fix = convert_ultima_acute_to_grave(fix)

        suggestions.append(fix)

    return ' '.join(suggestions)


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


def finalize_sequence(unaccented_sequence, valid_unaccented, rahlfs_words, swete_words,
                       ctx, prev_accented, next_word, errors, enclitic_pairs,
                       is_end_of_verse=False):
    """Process a completed unaccented sequence and add to appropriate list.

    Args:
        is_end_of_verse: True if this sequence ends at the end of the verse
    """
    if not unaccented_sequence:
        return

    result = classify_sequence(unaccented_sequence, valid_unaccented)
    suggested = suggest_fixes_for_sequence(
        unaccented_sequence, valid_unaccented, rahlfs_words, swete_words,
        ctx.line, is_end_of_verse
    )
    entry = {
        'line_num': ctx.line_num,
        'verse_ref': ctx.verse_ref,
        'unaccented_words': ' '.join(unaccented_sequence),
        'suggested_fix': suggested,
        'sequence_length': len(unaccented_sequence),
        'reason': result['reason'],
        'context_before': prev_accented or '',
        'context_after': next_word or '',
        'full_line': ctx.line
    }
    if result['category'] == 'error':
        errors.append(entry)
    elif result['category'] == 'enclitic_pair':
        enclitic_pairs.append(entry)


def process_brenton_file(brenton_path, valid_unaccented, rahlfs_words, swete_words):
    """Process Brenton.tex and find problematic unaccented sequences.

    Args:
        brenton_path: Path to Brenton.tex file
        valid_unaccented: Set of valid enclitic/proclitic forms
        rahlfs_words: Dict mapping normalized -> original from Rahlfs
        swete_words: Dict mapping normalized -> original from Swete

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
                # Sequence ends due to accented word
                finalize_sequence(unaccented_sequence, valid_unaccented, rahlfs_words, swete_words,
                                  ctx, prev_accented, word, errors, enclitic_pairs)
                # Reset sequence
                unaccented_sequence = []
                prev_accented = word
            else:
                # Unaccented word - add to sequence
                unaccented_sequence.append(word)

                # Check if this word is followed by punctuation (breaks sequence)
                if has_punctuation_after(word, ctx.line):
                    # End sequence here - punctuation breaks it
                    finalize_sequence(unaccented_sequence, valid_unaccented, rahlfs_words, swete_words,
                                      ctx, prev_accented, '', errors, enclitic_pairs)
                    # The word itself becomes the "previous" context for next sequence
                    prev_accented = word
                    unaccented_sequence = []

        # Check sequence at end of verse
        finalize_sequence(unaccented_sequence, valid_unaccented, rahlfs_words, swete_words,
                          ctx, prev_accented, '', errors, enclitic_pairs,
                          is_end_of_verse=True)

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
            'Suggested Fix',
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
                error.get('suggested_fix', ''),
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
        '--rahlfs-words',
        default='../input/rahlfs_words.csv',
        help='Path to Rahlfs word list (default: ../input/rahlfs_words.csv)'
    )
    parser.add_argument(
        '--swete-words',
        default='../input/swete_words.csv',
        help='Path to Swete word list (default: ../input/swete_words.csv)'
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

    print(f"Loading Rahlfs word list from {args.rahlfs_words}...")
    rahlfs_dict = load_words_with_ids(args.rahlfs_words)
    rahlfs_words = derive_word_set(rahlfs_dict)
    print(f"  Loaded {len(rahlfs_words)} unique word forms")

    print(f"Loading Swete word list from {args.swete_words}...")
    swete_dict = load_words_with_ids(args.swete_words)
    swete_words = derive_word_set(swete_dict)
    print(f"  Loaded {len(swete_words)} unique word forms")

    print(f"Detecting problematic unaccented words in {args.input}...")
    errors, enclitic_pairs = process_brenton_file(
        args.input, valid_unaccented, rahlfs_words, swete_words
    )

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
