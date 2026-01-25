#!/usr/bin/env python3
"""
Detect breathing mark errors in Brenton Septuagint.

Detection logic (rules-based):
1. Missing breathing marks:
   - Initial vowel/diphthong without breathing
   - Initial ρ without rough breathing
   - Crasis forms missing expected breathing

2. Wrong breathing position:
   - Breathing on wrong vowel in diphthong (first instead of second)
   - Breathing not on first vowel of word

3. Wrong breathing type:
   - Smooth breathing on initial ρ (should be rough)
   - Smooth breathing on initial υ (should be rough)

4. Interior rho errors:
   - Single interior ρ with breathing mark
   - Double ρρ without proper ῤῥ pattern
   - Double ρρ with wrong pattern (ῥῥ, ῤῤ, partial)

5. Consonant-initial words with breathing (crasis):
   - Only valid for known crasis forms
   - Crasis forms must have correct breathing
"""

import argparse
import csv
import sys
import unicodedata
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.greek_utils import normalize_text, strip_diacritics
from shared.brenton_parser import BrentonParser
from shared.data_loaders import load_words_with_ids, derive_word_set

# Unicode constants for breathing marks
SMOOTH_BREATHING = '\u0313'  # combining comma above (psili)
ROUGH_BREATHING = '\u0314'   # combining reversed comma above (dasia)

# Greek vowels (base characters only)
VOWELS = set('αεηιουωΑΕΗΙΟΥΩ')
VOWELS_LOWER = set('αεηιουω')

# Greek diphthongs where breathing goes on 2nd letter when word-initial
# Note: ωυ excluded - doesn't appear as initial form in LXX
# Note: A dieresis (διαλυτικά) on the second vowel indicates it's NOT a diphthong
DIPHTHONGS = {'αι', 'αυ', 'ει', 'ευ', 'οι', 'ου', 'ηυ', 'υι'}

# Unicode for dieresis (indicates vowels are pronounced separately, not as diphthong)
DIAERESIS = '\u0308'  # COMBINING DIAERESIS

# Greek consonants (for detecting consonant-initial words)
CONSONANTS = set('βγδζθκλμνξπρσςτφχψΒΓΔΖΘΚΛΜΝΞΠΡΣΤΦΧΨ')


@dataclass
class WordStartInfo:
    """Information about how a word starts."""
    starts_with_vowel: bool
    starts_with_diphthong: bool
    starts_with_rho: bool
    starts_with_consonant: bool  # other than ρ
    first_vowel_position: int  # -1 if no vowel
    expected_breathing_position: int  # where breathing should be (-1 if no breathing expected)
    diphthong_letters: str  # the diphthong if starts_with_diphthong, else ''


@dataclass
class BreathingInfo:
    """Information about breathing marks in a word."""
    has_breathing: bool
    breathing_type: Optional[str]  # 'smooth', 'rough', or None
    breathing_position: int  # position in base characters (-1 if none)
    breathing_char_index: int  # index in NFD string (-1 if none)
    all_breathings: List[Tuple[int, str, int]]  # list of (position, type, nfd_index)


@dataclass
class BreathingError:
    """A detected breathing mark error."""
    error_type: str
    description: str


def get_base_chars(word: str) -> List[Tuple[str, int]]:
    """Get base characters from a word with their NFD indices.

    Returns list of (base_char, nfd_start_index) tuples.
    """
    nfd = unicodedata.normalize('NFD', normalize_text(word))
    base_chars = []

    for i, char in enumerate(nfd):
        if unicodedata.category(char) != 'Mn':  # Not a combining mark
            base_chars.append((char, i))

    return base_chars


def get_word_start_info(word: str) -> WordStartInfo:
    """Analyze how a word starts to determine breathing requirements."""
    nfd = unicodedata.normalize('NFD', normalize_text(word))
    base_chars = get_base_chars(word)

    if not base_chars:
        return WordStartInfo(
            starts_with_vowel=False,
            starts_with_diphthong=False,
            starts_with_rho=False,
            starts_with_consonant=False,
            first_vowel_position=-1,
            expected_breathing_position=-1,
            diphthong_letters=''
        )

    first_char = base_chars[0][0].lower()

    # Check for initial ρ
    if first_char == 'ρ':
        return WordStartInfo(
            starts_with_vowel=False,
            starts_with_diphthong=False,
            starts_with_rho=True,
            starts_with_consonant=False,
            first_vowel_position=0,  # ρ acts like vowel for breathing purposes
            expected_breathing_position=0,
            diphthong_letters=''
        )

    # Check for initial vowel
    if first_char in VOWELS_LOWER:
        # Check for diphthong
        if len(base_chars) >= 2:
            second_char = base_chars[1][0].lower()
            potential_diphthong = first_char + second_char
            if potential_diphthong in DIPHTHONGS:
                # Check if second vowel has dieresis - if so, NOT a diphthong
                # Dieresis indicates the vowels are pronounced separately
                second_char_nfd_idx = base_chars[1][1]
                has_dieresis = False
                for j in range(second_char_nfd_idx + 1, len(nfd)):
                    c = nfd[j]
                    if unicodedata.category(c) != 'Mn':
                        break  # Hit next base character
                    if c == DIAERESIS:
                        has_dieresis = True
                        break

                if not has_dieresis:
                    return WordStartInfo(
                        starts_with_vowel=True,
                        starts_with_diphthong=True,
                        starts_with_rho=False,
                        starts_with_consonant=False,
                        first_vowel_position=0,
                        expected_breathing_position=1,  # 2nd letter of diphthong
                        diphthong_letters=potential_diphthong
                    )

        # Single vowel start
        return WordStartInfo(
            starts_with_vowel=True,
            starts_with_diphthong=False,
            starts_with_rho=False,
            starts_with_consonant=False,
            first_vowel_position=0,
            expected_breathing_position=0,
            diphthong_letters=''
        )

    # Starts with consonant (not ρ)
    # Find first vowel position
    first_vowel_pos = -1
    for i, (char, _) in enumerate(base_chars):
        if char.lower() in VOWELS_LOWER:
            first_vowel_pos = i
            break

    return WordStartInfo(
        starts_with_vowel=False,
        starts_with_diphthong=False,
        starts_with_rho=False,
        starts_with_consonant=True,
        first_vowel_position=first_vowel_pos,
        expected_breathing_position=-1,  # consonant-initial words don't normally have breathing
        diphthong_letters=''
    )


def get_breathing_info(word: str) -> BreathingInfo:
    """Find all breathing marks in a word."""
    nfd = unicodedata.normalize('NFD', normalize_text(word))
    base_chars = get_base_chars(word)

    all_breathings = []
    current_base_pos = -1

    for i, char in enumerate(nfd):
        if unicodedata.category(char) != 'Mn':
            current_base_pos += 1
        else:
            code = ord(char)
            if code == ord(SMOOTH_BREATHING):
                all_breathings.append((current_base_pos, 'smooth', i))
            elif code == ord(ROUGH_BREATHING):
                all_breathings.append((current_base_pos, 'rough', i))

    if not all_breathings:
        return BreathingInfo(
            has_breathing=False,
            breathing_type=None,
            breathing_position=-1,
            breathing_char_index=-1,
            all_breathings=[]
        )

    # Return info about first breathing mark
    first = all_breathings[0]
    return BreathingInfo(
        has_breathing=True,
        breathing_type=first[1],
        breathing_position=first[0],
        breathing_char_index=first[2],
        all_breathings=all_breathings
    )


def check_interior_rho(word: str) -> List[BreathingError]:
    """Check for interior rho errors.

    Rules:
    - Single interior ρ should NOT have breathing
    - Double ρρ inside word SHOULD have ῤῥ pattern (smooth, rough)
    """
    errors = []
    nfd = unicodedata.normalize('NFD', normalize_text(word))
    base_chars = get_base_chars(word)

    if len(base_chars) < 2:
        return errors

    # Find all ρ positions (excluding first character)
    rho_positions = []
    for i, (char, nfd_idx) in enumerate(base_chars):
        if i > 0 and char.lower() == 'ρ':
            rho_positions.append((i, nfd_idx))

    if not rho_positions:
        return errors

    # Check for breathing on each interior ρ
    def has_breathing_at(base_pos: int) -> Tuple[bool, Optional[str]]:
        """Check if base character at position has breathing mark."""
        nfd = unicodedata.normalize('NFD', normalize_text(word))
        current_pos = -1
        for i, char in enumerate(nfd):
            if unicodedata.category(char) != 'Mn':
                current_pos += 1
            elif current_pos == base_pos:
                code = ord(char)
                if code == ord(SMOOTH_BREATHING):
                    return True, 'smooth'
                elif code == ord(ROUGH_BREATHING):
                    return True, 'rough'
        return False, None

    # Look for consecutive ρρ pairs
    i = 0
    while i < len(rho_positions):
        pos, nfd_idx = rho_positions[i]

        # Check if next character is also ρ (forming ρρ)
        is_double_rho = False
        if i + 1 < len(rho_positions):
            next_pos, _ = rho_positions[i + 1]
            if next_pos == pos + 1:
                is_double_rho = True

        if is_double_rho:
            # Check double ρρ pattern - should be ῤῥ
            first_has, first_type = has_breathing_at(pos)
            second_has, second_type = has_breathing_at(pos + 1)

            if not first_has and not second_has:
                errors.append(BreathingError(
                    error_type='double_rho_no_breathing',
                    description=f'Interior ρρ at position {pos}-{pos+1} missing ῤῥ breathing marks'
                ))
            elif first_has and second_has:
                if first_type != 'smooth' or second_type != 'rough':
                    errors.append(BreathingError(
                        error_type='double_rho_wrong_pattern',
                        description=f'Interior ρρ at position {pos}-{pos+1} has wrong pattern (should be ῤῥ, got {first_type}/{second_type})'
                    ))
            else:
                # Only one has breathing
                errors.append(BreathingError(
                    error_type='double_rho_partial_breathing',
                    description=f'Interior ρρ at position {pos}-{pos+1} has partial breathing (should be ῤῥ)'
                ))

            i += 2  # Skip both ρ in the pair
        else:
            # Single interior ρ - should NOT have breathing
            has, btype = has_breathing_at(pos)
            if has:
                errors.append(BreathingError(
                    error_type='single_interior_rho_with_breathing',
                    description=f'Single interior ρ at position {pos} has {btype} breathing (should have none)'
                ))
            i += 1

    return errors


def load_crasis_allowlist(filepath: str) -> Dict[str, str]:
    """Load crasis allowlist.

    Returns dict mapping normalized (stripped) form -> correct form with diacritics.
    """
    crasis_dict = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Store with key = stripped lowercase, value = original
                normalized = strip_diacritics(normalize_text(line)).lower()
                crasis_dict[normalized] = normalize_text(line)
    except FileNotFoundError:
        print(f"Warning: Crasis allowlist '{filepath}' not found. Continuing without it.")
    return crasis_dict


def is_known_crasis(word: str, crasis_dict: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """Check if word is a known crasis form.

    Returns (is_crasis, correct_form).
    """
    normalized = strip_diacritics(normalize_text(word)).lower()
    if normalized in crasis_dict:
        return True, crasis_dict[normalized]
    return False, None


def check_breathing_errors(word: str, crasis_dict: Dict[str, str]) -> List[BreathingError]:
    """Main function to check for all breathing mark errors in a word."""
    errors = []

    word = normalize_text(word)
    start_info = get_word_start_info(word)
    breathing_info = get_breathing_info(word)

    # Skip all-caps words (headings/titles)
    stripped = strip_diacritics(word)
    if stripped.isupper() and len(stripped) > 1:
        return errors

    # Check for multiple breathing marks (should never have more than one)
    # Exception: valid ῤῥ pattern on double rho contributes 2 breathing marks
    if len(breathing_info.all_breathings) > 1:
        base_chars = get_base_chars(word)

        # Find and exclude valid ῤῥ patterns from the count
        excluded_positions = set()
        breathings = breathing_info.all_breathings
        for i in range(len(breathings) - 1):
            pos1, type1, _ = breathings[i]
            pos2, type2, _ = breathings[i + 1]
            # Check if this pair is a valid ῤῥ pattern
            if (pos1 < len(base_chars) and pos2 < len(base_chars) and
                base_chars[pos1][0].lower() == 'ρ' and base_chars[pos2][0].lower() == 'ρ' and
                pos2 == pos1 + 1 and type1 == 'smooth' and type2 == 'rough'):
                excluded_positions.add(pos1)
                excluded_positions.add(pos2)

        # Count remaining breathing marks (not part of valid ῤῥ)
        remaining = [(pos, btype) for pos, btype, _ in breathings if pos not in excluded_positions]

        if len(remaining) > 1:
            positions = [str(pos) for pos, _ in remaining]
            errors.append(BreathingError(
                error_type='multiple_breathing_marks',
                description=f'Word has {len(remaining)} breathing marks (excluding valid ῤῥ) at positions {", ".join(positions)}'
            ))
            # Return early - no need to check other breathing errors if we have multiple marks
            return errors

    # Check interior rho errors first (applies regardless of word start type)
    rho_errors = check_interior_rho(word)
    errors.extend(rho_errors)

    # === Category 1 & 2: Initial vowel/diphthong ===
    if start_info.starts_with_vowel:
        if not breathing_info.has_breathing:
            # Missing breathing on initial vowel/diphthong
            if start_info.starts_with_diphthong:
                errors.append(BreathingError(
                    error_type='missing_breathing_diphthong',
                    description=f'Initial diphthong {start_info.diphthong_letters} missing breathing mark on second letter'
                ))
            else:
                errors.append(BreathingError(
                    error_type='missing_breathing_vowel',
                    description='Initial vowel missing breathing mark'
                ))
        else:
            # Has breathing - check position
            if breathing_info.breathing_position != start_info.expected_breathing_position:
                if start_info.starts_with_diphthong:
                    if breathing_info.breathing_position == 0:
                        errors.append(BreathingError(
                            error_type='breathing_wrong_vowel_diphthong',
                            description=f'Breathing on first vowel of diphthong {start_info.diphthong_letters}, should be on second'
                        ))
                    else:
                        errors.append(BreathingError(
                            error_type='breathing_wrong_position',
                            description=f'Breathing at position {breathing_info.breathing_position}, expected at {start_info.expected_breathing_position}'
                        ))
                else:
                    errors.append(BreathingError(
                        error_type='breathing_not_on_first_vowel',
                        description=f'Breathing at position {breathing_info.breathing_position}, should be on first vowel (position 0)'
                    ))

            # Check breathing type for initial υ (only when υ is the FIRST letter, not in diphthongs)
            # The rule is: υ always has rough breathing when it's the first letter of a word
            # When υ is part of a diphthong (αυ, ευ, ου, etc.), this rule doesn't apply
            if not start_info.starts_with_diphthong:
                base_chars = get_base_chars(word)
                if base_chars and base_chars[0][0].lower() == 'υ' and breathing_info.breathing_type == 'smooth':
                    errors.append(BreathingError(
                        error_type='smooth_on_initial_upsilon',
                        description='Initial υ has smooth breathing, should always be rough'
                    ))

    # === Category 3: Initial ρ ===
    elif start_info.starts_with_rho:
        if not breathing_info.has_breathing:
            errors.append(BreathingError(
                error_type='missing_rough_on_rho',
                description='Initial ρ missing rough breathing mark'
            ))
        elif breathing_info.breathing_position != 0:
            errors.append(BreathingError(
                error_type='breathing_not_on_rho',
                description=f'Breathing at position {breathing_info.breathing_position}, should be on initial ρ (position 0)'
            ))
        elif breathing_info.breathing_type == 'smooth':
            errors.append(BreathingError(
                error_type='smooth_on_initial_rho',
                description='Initial ρ has smooth breathing, should be rough'
            ))

    # === Category 5: Consonant-initial words with breathing on VOWELS (crasis) ===
    elif start_info.starts_with_consonant:
        # Check if breathing is on a vowel (not on ρ - those are handled by interior rho checks)
        breathing_on_vowel = False
        if breathing_info.has_breathing:
            base_chars = get_base_chars(word)
            if breathing_info.breathing_position < len(base_chars):
                breathing_char = base_chars[breathing_info.breathing_position][0].lower()
                breathing_on_vowel = breathing_char in VOWELS_LOWER

        if breathing_on_vowel:
            # Consonant-initial word has breathing on a vowel - check if it's crasis
            is_crasis, correct_form = is_known_crasis(word, crasis_dict)

            if is_crasis:
                # It's a known crasis - verify it has correct form
                # Compare case-insensitively since allowlist may have both lowercase and capital versions
                if word.lower() != correct_form.lower():
                    errors.append(BreathingError(
                        error_type='crasis_wrong_form',
                        description=f'Crasis form incorrect, should be {correct_form}'
                    ))
            else:
                # Not a known crasis - unexpected breathing on vowel
                errors.append(BreathingError(
                    error_type='unexpected_breathing_consonant_initial',
                    description=f'Consonant-initial word has breathing on vowel at position {breathing_info.breathing_position} (not a known crasis form)'
                ))
        elif not breathing_info.has_breathing:
            # No breathing on consonant-initial word - check if it's a crasis missing breathing
            is_crasis, correct_form = is_known_crasis(word, crasis_dict)
            if is_crasis:
                errors.append(BreathingError(
                    error_type='crasis_missing_breathing',
                    description=f'Crasis form missing breathing, should be {correct_form}'
                ))

    # === Check for unexpected interior breathing on vowels ===
    # Only for vowel-initial or rho-initial words: check for additional breathing marks
    # beyond the expected initial position. Consonant-initial words are already handled
    # by the crasis/unexpected_breathing_consonant_initial checks above.
    if breathing_info.all_breathings and (start_info.starts_with_vowel or start_info.starts_with_rho):
        base_chars = get_base_chars(word)

        for pos, btype, _ in breathing_info.all_breathings:
            # Skip if this is at the expected initial breathing position
            if pos == start_info.expected_breathing_position:
                continue
            # Skip if on a rho (handled by interior rho checks)
            if pos < len(base_chars) and base_chars[pos][0].lower() == 'ρ':
                continue
            # Check if this breathing is on a vowel
            if pos < len(base_chars) and base_chars[pos][0].lower() in VOWELS_LOWER:
                errors.append(BreathingError(
                    error_type='unexpected_interior_breathing',
                    description=f'Unexpected {btype} breathing on interior vowel at position {pos} (possible merged words)'
                ))

    return errors


def suggest_fix(word: str, errors: List[BreathingError],
                swete_words: Dict[str, str], rahlfs_words: Dict[str, str],
                crasis_dict: Dict[str, str]) -> str:
    """Suggest a fix for a word with breathing errors.

    Uses Swete/Rahlfs dictionaries for lookups, falls back to rule-based fixes.
    """
    # First try dictionary lookup
    normalized = strip_diacritics(normalize_text(word)).lower()

    # Check Swete first, then Rahlfs
    if normalized in swete_words:
        suggestion = swete_words[normalized]
        # Preserve capitalization if original was capitalized
        if word and word[0].isupper() and suggestion and suggestion[0].islower():
            first_upper = suggestion[0].upper()
            if len(first_upper) == 1:
                suggestion = first_upper + suggestion[1:]
        return suggestion

    if normalized in rahlfs_words:
        suggestion = rahlfs_words[normalized]
        if word and word[0].isupper() and suggestion and suggestion[0].islower():
            first_upper = suggestion[0].upper()
            if len(first_upper) == 1:
                suggestion = first_upper + suggestion[1:]
        return suggestion

    # Check crasis dict
    if normalized in crasis_dict:
        return crasis_dict[normalized]

    # No dictionary match - return empty (could add rule-based fixes later)
    return ''


def is_all_caps(word: str) -> bool:
    """Check if word is all uppercase."""
    stripped = strip_diacritics(word)
    letters = [c for c in stripped if c.isalpha()]
    return len(letters) > 0 and all(c.isupper() for c in letters)


def process_brenton_file(brenton_path: str, crasis_dict: Dict[str, str],
                         swete_words: Dict[str, str], rahlfs_words: Dict[str, str]) -> List[dict]:
    """Process Brenton.tex and find breathing mark errors."""
    all_errors = []
    parser = BrentonParser(brenton_path)
    last_book = None

    for ctx in parser.parse():
        if ctx.book and ctx.book != last_book:
            print(f"Processing book: {ctx.book}")
            last_book = ctx.book

        if not ctx.has_complete_ref or not ctx.greek_words:
            continue

        for word in ctx.greek_words:
            # Skip all-caps words (headings)
            if is_all_caps(word):
                continue

            errors = check_breathing_errors(word, crasis_dict)

            if errors:
                # Get suggested fix
                suggested = suggest_fix(word, errors, swete_words, rahlfs_words, crasis_dict)

                for error in errors:
                    all_errors.append({
                        'line_num': ctx.line_num,
                        'verse_ref': ctx.verse_ref,
                        'word': word,
                        'suggested_fix': suggested,
                        'error_type': error.error_type,
                        'description': error.description,
                        'full_line': ctx.line
                    })

    return all_errors


def write_errors_tsv(errors: List[dict], output_path: str):
    """Write detected errors to TSV file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow([
            'Line Number',
            'Verse Reference',
            'Word',
            'Suggested Fix',
            'Error Type',
            'Full Line'
        ])
        for error in errors:
            writer.writerow([
                error['line_num'],
                error['verse_ref'],
                error['word'],
                error['suggested_fix'],
                error['error_type'],
                error['full_line']
            ])

    print(f"Wrote {len(errors)} errors to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Detect breathing mark errors in Brenton Septuagint'
    )
    parser.add_argument(
        '--input',
        default='../input/Brenton.tex',
        help='Path to input .tex file (default: ../input/Brenton.tex)'
    )
    parser.add_argument(
        '--crasis-allowlist',
        default='../input/crasis_allowlist.txt',
        help='Path to crasis allowlist (default: ../input/crasis_allowlist.txt)'
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
        default='output/breathing_errors.tsv',
        help='Output TSV file path (default: output/breathing_errors.tsv)'
    )

    args = parser.parse_args()

    print(f"Loading crasis allowlist from {args.crasis_allowlist}...")
    crasis_dict = load_crasis_allowlist(args.crasis_allowlist)
    print(f"  Loaded {len(crasis_dict)} crasis forms")

    print(f"Loading Rahlfs word list from {args.rahlfs_words}...")
    rahlfs_dict = load_words_with_ids(args.rahlfs_words)
    rahlfs_words = derive_word_set(rahlfs_dict)
    print(f"  Loaded {len(rahlfs_words)} unique word forms")

    print(f"Loading Swete word list from {args.swete_words}...")
    swete_dict = load_words_with_ids(args.swete_words)
    swete_words = derive_word_set(swete_dict)
    print(f"  Loaded {len(swete_words)} unique word forms")

    print(f"\nDetecting breathing mark errors in {args.input}...")
    errors = process_brenton_file(args.input, crasis_dict, swete_words, rahlfs_words)

    print(f"\nWriting results to {args.output}...")
    write_errors_tsv(errors, args.output)

    # Summary statistics
    print(f"\nSummary:")
    print(f"  Total errors found: {len(errors)}")

    # Count by error type
    by_type = {}
    for error in errors:
        etype = error['error_type']
        by_type[etype] = by_type.get(etype, 0) + 1

    if by_type:
        print(f"\n  Errors by type:")
        for etype in sorted(by_type.keys()):
            print(f"    {etype}: {by_type[etype]}")

    # Count unique words
    unique_words = set(error['word'] for error in errors)
    print(f"\n  Unique words with errors: {len(unique_words)}")


if __name__ == '__main__':
    main()
