#!/usr/bin/env python3
"""
Script to check for Greek words in Brenton.tex that are not found in
rahlfs_words.csv or swete_words.csv files.
"""

import unicodedata
import csv
import argparse
import sys
from pathlib import Path
from difflib import SequenceMatcher

# Add parent directory to path to import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.book_code_mappings import (
    convert_brenton_reference_to_rahlfs,
    convert_brenton_reference_to_swete
)
from shared.greek_utils import (
    strip_diacritics,
    normalize_for_comparison,
    load_accepted_words,
    load_already_examined
)
from shared.brenton_parser import BrentonParser
from shared.data_loaders import (
    derive_word_set,
    load_words_with_ids,
    load_versification,
    get_words_by_id_range,
    get_verse_words,
    get_area_words
)
from valid_variation_patterns import generate_variation_list, strip_accents as strip_accents_vvp

# Module-level global variables for loaded data
RAHLFS_WORDS_DICT = {}  # word_id -> {'normalized': str, 'original': str}
SWETE_WORDS_DICT = {}   # word_id -> {'normalized': str, 'original': str}
RAHLFS_WORDS = {}       # normalized -> original (derived from RAHLFS_WORDS_DICT)
SWETE_WORDS = {}        # normalized -> original (derived from SWETE_WORDS_DICT)
RAHLFS_VERSE_MAP = {}   # verse_ref -> word_id
SWETE_VERSE_MAP = {}    # verse_ref -> word_id
RAHLFS_SORTED_VERSES = []  # [(verse_ref, word_id), ...] sorted by word_id
SWETE_SORTED_VERSES = []   # [(verse_ref, word_id), ...] sorted by word_id
ACCEPTED_WORDS = set()  # set of normalized accepted words
ALREADY_EXAMINED = {}  # dict mapping (verse_ref, normalized_word) -> corrected_word


def is_likely_proper_name(word):
    """Check if a word is likely a proper name (starts with capital)."""
    # After normalization, check if the first character is uppercase
    return len(word) > 0 and word[0].isupper()


def is_likely_number_word(word):
    """Check if word appears to be a number/numeral."""
    # Greek number words often contain these patterns
    number_patterns = []
    word_lower = word.lower()
    word_stripped = strip_diacritics(word_lower)
    
    for pattern in number_patterns:
        pattern_stripped = strip_diacritics(pattern.lower())
        if pattern_stripped in word_stripped:
            return True
    return False


def find_closest_word(word, word_dict):
    """Find the closest matching word in the dict within max_distance edits.
    word_dict maps normalized -> original (with diacritics).
    Returns the original word with diacritics.
    
    Args:
        word: The word to match
        word_dict: Dictionary mapping normalized -> original words
    """
    normalized = strip_diacritics(word.lower())

    best_match_normalized, best_ratio = find_best_match(word_dict, normalized)
    
    # Return match only if it's very close (likely a typo)
    if best_ratio >= 0.80 and best_match_normalized:
        # Return original form with diacritics
        return word_dict[best_match_normalized], best_ratio
    else:
        # try adding ν if the word ends with a movable-nu-eligible ending
        # Movable ν can appear after: -ε, -ι
        if normalized.endswith('ε') or normalized.endswith('ι'):
            normalized_with_nu = normalized + 'ν'

            best_match_normalized, best_ratio = find_best_match(word_dict, normalized_with_nu, best_ratio)            
            
            # Check if adding ν improved the match to above threshold
            if best_ratio >= 0.80 and best_match_normalized:
                return word_dict[best_match_normalized], best_ratio
    
    return None, 0

def find_best_match(word_dict, normalized, current_best_ratio = 0):
    # Only check words of similar length (within 2 characters)
    # Normalize the search term for comparison
    normalized_for_comp = normalize_for_comparison(normalized)
    target_len = len(normalized_for_comp)
    
    best_match_normalized = None
    for candidate_normalized in word_dict.keys():
        # Normalize candidate for comparison (handles spaces and ς/σ)
        candidate_for_comp = normalize_for_comparison(candidate_normalized)
        if abs(len(candidate_for_comp) - target_len) > 2:
            continue
            
        # Calculate similarity ratio
        ratio = SequenceMatcher(None, normalized_for_comp, candidate_for_comp).ratio()
        
        # If very similar (>0.8 similarity), it might be a typo
        if ratio > current_best_ratio:
            current_best_ratio = ratio
            best_match_normalized = candidate_normalized
    return best_match_normalized,current_best_ratio


def check_words_in_both_sources(word, rahlfs_words, swete_words, check_func):
    """
    Helper to check word in both Rahlfs and Swete word sources.
    
    Args:
        word: The word to check
        rahlfs_words: Dictionary of Rahlfs words
        swete_words: Dictionary of Swete words
        check_func: Function to call with (word, word_dict) that returns (found, match, score)
    
    Returns:
        (found, best_match, best_score) tuple
    """
    found_r, match_r, score_r = check_func(word, rahlfs_words)
    found_s, match_s, score_s = check_func(word, swete_words)
    
    if found_r or found_s:
        best_match = match_r if (found_r and score_r >= score_s) else match_s
        best_score = max(score_r, score_s)
        return True, best_match, best_score
    
    return False, None, 0


def has_legitimate_variation_in_verse(word, verse_words):
    """
    Check if any legitimate spelling variation of word exists in verse_words.
    
    Args:
        word: The Brenton word to check
        verse_words: Dictionary mapping normalized -> original for words in the verse
    
    Returns:
        (has_variation, matched_word, variation_count) tuple
        - has_variation: True if a variation was found
        - matched_word: The original form (with diacritics) from verse_words that matched
        - variation_count: Number of variations generated
    """
    if not verse_words:
        return False, None, 0
    
    # Generate all legitimate variations of the word
    variations = generate_variation_list(word, "all")
    
    # Check if any variation exists in the verse words
    # Normalize both for comparison (handles spaces and ς/σ)
    for variation in variations:
        variation_normalized = normalize_for_comparison(variation)
        for normalized_key, original_value in verse_words.items():
            key_normalized = normalize_for_comparison(normalized_key)
            if variation_normalized == key_normalized:
                return True, original_value, len(variations)
    
    return False, None, len(variations)


def check_legitimate_variations_in_scope(word, rahlfs_words, swete_words):
    """
    Check for legitimate variations in both Rahlfs and Swete word sources.
    
    Returns:
        (found, matched_word, score) tuple
    """
    return check_words_in_both_sources(word, rahlfs_words, swete_words, has_legitimate_variation_in_verse)


def check_typos_in_scope(word, rahlfs_words, swete_words):
    """
    Check for typos in both Rahlfs and Swete word sources.
    
    Returns:
        (found, matched_word, similarity_ratio) tuple
    """
    def find_typo(w, word_dict):
        closest, ratio = find_closest_word(w, word_dict)
        found = ratio >= 0.80
        return found, closest, ratio
    
    return check_words_in_both_sources(word, rahlfs_words, swete_words, find_typo)


def is_likely_typo(word, brenton_book=None, brenton_ch=None, brenton_vs=None):
    """
    Check if word is likely a typo by finding very similar words.
    Uses global data structures (RAHLFS_WORDS_DICT, SWETE_WORDS_DICT, etc.).
    First checks verse-specific words for legitimate variations, then exact matches,
    then area (±20 verses), then falls back to broader corpus.
    Compound words are automatically checked since get_verse_words includes them.
    Returns (is_typo, closest_match, similarity_ratio, verse_match, area_match, legitimate_variation)
    """
    verse_match = False
    area_match = False
    legitimate_variation = False
    
    # First try verse-specific search if we have the necessary data
    if all([brenton_book, brenton_ch, brenton_vs, RAHLFS_VERSE_MAP, SWETE_VERSE_MAP, 
            RAHLFS_SORTED_VERSES, SWETE_SORTED_VERSES,
            RAHLFS_WORDS_DICT, SWETE_WORDS_DICT]):
        try:
            rahlfs_ref = convert_brenton_reference_to_rahlfs(brenton_book, brenton_ch, brenton_vs)
            swete_ref = convert_brenton_reference_to_swete(brenton_book, brenton_ch, brenton_vs)
            
            rahlfs_verse_words = get_verse_words(rahlfs_ref, RAHLFS_VERSE_MAP, RAHLFS_SORTED_VERSES, RAHLFS_WORDS_DICT)
            swete_verse_words = get_verse_words(swete_ref, SWETE_VERSE_MAP, SWETE_SORTED_VERSES, SWETE_WORDS_DICT)
            
            if rahlfs_verse_words or swete_verse_words:
                # Check for legitimate spelling variations in the verse
                has_var, best_match, _ = check_legitimate_variations_in_scope(word, rahlfs_verse_words, swete_verse_words)
                
                if has_var:
                    # Found a legitimate variation - not a typo!
                    return False, best_match, 1.0, True, False, True
                
                # Check verse-specific words for typos
                is_typo, best_match, best_ratio = check_typos_in_scope(word, rahlfs_verse_words, swete_verse_words)
                
                if is_typo:
                    return True, best_match, best_ratio, True, False, False
            
            # If not found in exact verse, check surrounding area (±20 verses)
            rahlfs_area_words = get_area_words(rahlfs_ref, RAHLFS_VERSE_MAP, RAHLFS_SORTED_VERSES, RAHLFS_WORDS_DICT, verse_range=20)
            swete_area_words = get_area_words(swete_ref, SWETE_VERSE_MAP, SWETE_SORTED_VERSES, SWETE_WORDS_DICT, verse_range=20)
            
            if rahlfs_area_words or swete_area_words:
                # Check for legitimate variations in the area
                has_var, best_match, _ = check_legitimate_variations_in_scope(word, rahlfs_area_words, swete_area_words)
                
                if has_var:
                    # Found a legitimate variation in the area - not a typo!
                    return False, best_match, 1.0, False, True, True
                
                # Check area words for typos
                is_typo, best_match, best_ratio = check_typos_in_scope(word, rahlfs_area_words, swete_area_words)
                
                if is_typo:
                    return True, best_match, best_ratio, False, True, False
        except Exception:
            # If conversion or verse lookup fails, continue to broad search
            pass
    
    # Fall back to broad corpus search - use pre-derived global word sets
    is_typo, best_match, best_ratio = check_typos_in_scope(word, RAHLFS_WORDS, SWETE_WORDS)
    
    if is_typo:
        return True, best_match, best_ratio, False, False, False
    return False, None, 0, False, False, False


def is_word_in_sets(word):
    """Check if word exists in either word dict (case-insensitive, diacritic-stripped).
    Uses global RAHLFS_WORDS and SWETE_WORDS (pre-derived normalized->original mappings).
    """
    normalized = strip_diacritics(word.lower())
    
    # First, try the word as-is
    if normalized in RAHLFS_WORDS or normalized in SWETE_WORDS:
        return True
    
    # Second, try with movable ν added at the end
    # This handles cases where Brenton drops the movable nu
    normalized_with_nu = normalized + 'ν'
    if normalized_with_nu in RAHLFS_WORDS or normalized_with_nu in SWETE_WORDS:
        return True
    
    return False


def process_bible_file(bible_path, output_path, check_typos=True):
    """Process the Bible file and log missing words.
    Uses global data structures (RAHLFS_WORDS_DICT, SWETE_WORDS_DICT, ACCEPTED_WORDS, etc.).
    """
    missing_words = []
    words_checked = 0
    typos_found = 0
    last_book = None

    print("Processing Bible file...")
    if not check_typos:
        print("Typo checking disabled for faster processing.")

    parser = BrentonParser(bible_path)

    for ctx in parser.parse():
        # Print book progress
        if ctx.book and ctx.book != last_book:
            print(f"Found book: {ctx.book}")
            last_book = ctx.book

        if not ctx.greek_words:
            continue

        # Use verse_ref from parser if complete, otherwise "Unknown"
        verse_ref = ctx.verse_ref if ctx.has_complete_ref else "Unknown"

        for word in ctx.greek_words:
            # First check if word is in accepted words list (skip if accepted)
            if ACCEPTED_WORDS:
                normalized_word = strip_diacritics(word.lower())
                if normalized_word in ACCEPTED_WORDS:
                    continue

            # Check if this word has already been examined in this verse
            if ALREADY_EXAMINED and ctx.has_complete_ref:
                normalized_word = strip_diacritics(word.lower())
                key = (ctx.verse_ref, normalized_word)
                if key in ALREADY_EXAMINED:
                    continue

            if not is_word_in_sets(word):
                # Check if likely proper name
                is_name = is_likely_proper_name(word) if check_typos else False

                # Check if likely number word
                is_number = is_likely_number_word(word) if check_typos else False

                # Check if likely typo (with optional verse-specific checking)
                if check_typos:
                    words_checked += 1
                    if words_checked % 100 == 0:
                        print(f"  Checked {words_checked} words, found {typos_found} potential typos so far... (Current: {verse_ref})")

                    is_typo, closest_match, similarity, verse_match, area_match, legitimate_variation = is_likely_typo(
                        word, ctx.book, ctx.chapter, ctx.verse
                    )

                    if is_typo:
                        typos_found += 1
                else:
                    is_typo, closest_match, similarity, verse_match, area_match, legitimate_variation = False, None, 0, False, False, False

                missing_words.append({
                    'line_num': ctx.line_num,
                    'verse_ref': verse_ref,
                    'word': word,
                    'full_line': ctx.line,
                    'is_name': is_name,
                    'is_number': is_number,
                    'is_typo': is_typo,
                    'closest_match': closest_match if closest_match else '',
                    'similarity': f"{similarity:.2f}" if similarity > 0 else '',
                    'verse_match': verse_match,
                    'area_match': area_match,
                    'legitimate_variation': legitimate_variation
                })
    
    # Write results to log file
    print(f"\nWriting results to {output_path}...")
    print(f"Opening file for writing: {output_path}")
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        print(f"Successfully opened {output_path} for writing")
        writer = csv.writer(f, delimiter='\t')
        # Write header - simple format without typo check columns
        writer.writerow(['Line Number', 'Verse Reference', 'Word', 'Full Line'])
        
        # Write data
        for entry in missing_words:
            writer.writerow([
                entry['line_num'],
                entry['verse_ref'],
                entry['word'],
                entry['full_line']
            ])
        print(f"Finished writing {len(missing_words)} rows to {output_path}")
    
    # Write full typo check results if enabled
    if check_typos:
        typo_check_path = output_path.replace('.tsv', '_typo_check.tsv')
        print(f"Writing full typo check results to {typo_check_path}...")
        print(f"Opening file for writing: {typo_check_path}")
        with open(typo_check_path, 'w', encoding='utf-8', newline='') as f:
            print(f"Successfully opened {typo_check_path} for writing")
            writer = csv.writer(f, delimiter='\t')
            # Write header with all columns including verse match, area match, and legitimate variation
            writer.writerow(['Line Number', 'Verse Reference', 'Word', 'Is Name?', 'Is Number?', 
                            'Likely Typo?', 'Closest Match', 'Similarity', 'Verse Match?', 'Area Match?', 
                            'Legitimate Variation?', 'Full Line'])
            
            # Write data
            for entry in missing_words:
                writer.writerow([
                    entry['line_num'],
                    entry['verse_ref'],
                    entry['word'],
                    'Yes' if entry['is_name'] else 'No',
                    'Yes' if entry['is_number'] else 'No',
                    'Yes' if entry['is_typo'] else 'No',
                    entry['closest_match'],
                    entry['similarity'],
                    'Yes' if entry.get('verse_match', False) else 'No',
                    'Yes' if entry.get('area_match', False) else 'No',
                    'Yes' if entry.get('legitimate_variation', False) else 'No',
                    entry['full_line']
                ])
            print(f"Finished writing {len(missing_words)} rows to {typo_check_path}")
    
    # Create a filtered file with likely typos only (excluding legitimate variations)
    if check_typos:
        filtered_path = output_path.replace('.tsv', '_likely_typos.tsv')
        likely_typos = [e for e in missing_words 
                       if e['is_typo'] and not e['is_number'] 
                       and not e.get('legitimate_variation', False)]
        
        print(f"Writing likely typos to {filtered_path}...")
        print(f"Opening file for writing: {filtered_path}")
        with open(filtered_path, 'w', encoding='utf-8', newline='') as f:
            print(f"Successfully opened {filtered_path} for writing")
            writer = csv.writer(f, delimiter='\t')
            # Write header with verse match and area match columns
            writer.writerow(['Line Number', 'Verse Reference', 'Word', 'Closest Match', 'Similarity', 'Verse Match?', 'Area Match?', 'Full Line'])
            
            # Write data
            for entry in likely_typos:
                writer.writerow([
                    entry['line_num'],
                    entry['verse_ref'],
                    entry['word'],
                    entry['closest_match'],
                    entry['similarity'],
                    'Yes' if entry.get('verse_match', False) else 'No',
                    'Yes' if entry.get('area_match', False) else 'No',
                    entry['full_line']
                ])
            print(f"Finished writing {len(likely_typos)} rows to {filtered_path}")
        
        # Create a separate file for legitimate variations found
        variations_path = output_path.replace('.tsv', '_legitimate_variations.tsv')
        legitimate_variations = [e for e in missing_words if e.get('legitimate_variation', False)]
        
        print(f"Writing legitimate variations to {variations_path}...")
        print(f"Opening file for writing: {variations_path}")
        with open(variations_path, 'w', encoding='utf-8', newline='') as f:
            print(f"Successfully opened {variations_path} for writing")
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['Line Number', 'Verse Reference', 'Word', 'Matched Variation', 'Verse Match?', 'Area Match?', 'Full Line'])

            for entry in legitimate_variations:
                writer.writerow([
                    entry['line_num'],
                    entry['verse_ref'],
                    entry['word'],
                    entry['closest_match'],
                    'Yes' if entry.get('verse_match', False) else 'No',
                    'Yes' if entry.get('area_match', False) else 'No',
                    entry['full_line']
                ])
            print(f"Finished writing {len(legitimate_variations)} rows to {variations_path}")

        # Create a file for unmatched words (not legitimate variations, not confirmed numbers)
        # These are words that need manual review
        unmatched_path = output_path.replace('.tsv', '_unmatched.tsv')
        unmatched = [e for e in missing_words
                    if not e.get('legitimate_variation', False)
                    and not e['is_number']]

        print(f"Writing unmatched words to {unmatched_path}...")
        print(f"Opening file for writing: {unmatched_path}")
        with open(unmatched_path, 'w', encoding='utf-8', newline='') as f:
            print(f"Successfully opened {unmatched_path} for writing")
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['Line Number', 'Verse Reference', 'Word', 'Is Name?',
                            'Likely Typo?', 'Closest Match', 'Similarity', 'Full Line'])

            for entry in unmatched:
                writer.writerow([
                    entry['line_num'],
                    entry['verse_ref'],
                    entry['word'],
                    'Yes' if entry['is_name'] else 'No',
                    'Yes' if entry['is_typo'] else 'No',
                    entry['closest_match'],
                    entry['similarity'],
                    entry['full_line']
                ])
            print(f"Finished writing {len(unmatched)} rows to {unmatched_path}")

    print(f"\nComplete! Found {len(missing_words)} missing words.")
    if check_typos:
        print(f"  - Likely proper names: {sum(1 for e in missing_words if e['is_name'])}")
        print(f"  - Likely numbers: {sum(1 for e in missing_words if e['is_number'])}")
        print(f"  - Legitimate variations: {sum(1 for e in missing_words if e.get('legitimate_variation', False))}")
        legitimate_variations = [e for e in missing_words if e.get('legitimate_variation', False)]
        if legitimate_variations:
            verse_var = sum(1 for e in legitimate_variations if e.get('verse_match', False))
            area_var = sum(1 for e in legitimate_variations if e.get('area_match', False))
            print(f"    - Found in verse: {verse_var}")
            print(f"    - Found in area (±20 verses): {area_var}")
        
        likely_typos = [e for e in missing_words 
                       if e['is_typo'] and not e['is_number'] 
                       and not e.get('legitimate_variation', False)]
        print(f"  - Likely typos: {len(likely_typos)}")
        if likely_typos:
            verse_matches = sum(1 for e in likely_typos if e.get('verse_match', False))
            area_matches = sum(1 for e in likely_typos if e.get('area_match', False))
            corpus_matches = len(likely_typos) - verse_matches - area_matches
            print(f"    - Matched within verse: {verse_matches}")
            print(f"    - Matched within area (±20 verses): {area_matches}")
            print(f"    - Matched in broader corpus: {corpus_matches}")
        unmatched = [e for e in missing_words
                    if not e.get('legitimate_variation', False)
                    and not e['is_number']]
        print(f"  - Unmatched (need review): {len(unmatched)}")
    print(f"Results saved to: {output_path}")
    if check_typos:
        print(f"Full typo check results saved to: {typo_check_path}")
        print(f"Filtered typos saved to: {filtered_path}")
        print(f"Legitimate variations saved to: {variations_path}")
        print(f"Unmatched words saved to: {unmatched_path}")


def main():
    """Main entry point."""
    global RAHLFS_WORDS_DICT, SWETE_WORDS_DICT, RAHLFS_WORDS, SWETE_WORDS
    global RAHLFS_VERSE_MAP, SWETE_VERSE_MAP
    global RAHLFS_SORTED_VERSES, SWETE_SORTED_VERSES, ACCEPTED_WORDS, ALREADY_EXAMINED
    
    parser = argparse.ArgumentParser(
        description='Check for Greek words in Bible file that are not found in reference word lists.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with typo checking (default):
  python check_missing_words_for_typos.py

  # Run without typo checking (faster):
  python check_missing_words_for_typos.py --no-typo-check

  # Specify custom input files:
  python check_missing_words_for_typos.py --bible MyBible.tex --rahlfs rahlfs.csv
        """
    )
    
    parser.add_argument('--bible', default='../input/Brenton.tex',
                        help='Path to Bible .tex file (default: ../input/Brenton.tex)')
    parser.add_argument('--rahlfs', default='../input/rahlfs_words.csv',
                        help='Path to Rahlfs words CSV file (default: ../input/rahlfs_words.csv)')
    parser.add_argument('--swete', default='../input/swete_words.csv',
                        help='Path to Swete words CSV file (default: ../input/swete_words.csv)')
    parser.add_argument('--rahlfs-versification', default='../input/rahlfs_versification.csv',
                        help='Path to Rahlfs versification CSV file (default: ../input/rahlfs_versification.csv)')
    parser.add_argument('--swete-versification', default='../input/swete_versification.csv',
                        help='Path to Swete versification CSV file (default: ../input/swete_versification.csv)')
    parser.add_argument('--output', default='output/missing_words.tsv',
                        help='Path to output TSV file (default: output/missing_words.tsv)')
    parser.add_argument('--accepted-words', default='../accepted_words.txt',
                        help='Path to accepted words file (default: ../accepted_words.txt)')
    parser.add_argument('--already-examined', default='../word_corrections.tsv',
                        help='Path to already examined word changes file (default: ../word_corrections.tsv)')
    parser.add_argument('--no-typo-check', action='store_true',
                        help='Disable typo checking for faster processing')
    
    args = parser.parse_args()
    
    # File paths
    bible_path = args.bible
    output_path = args.output
    check_typos = not args.no_typo_check
    
    print("Loading word data...")
    
    # Load word IDs into global variables (single CSV read per file)
    RAHLFS_WORDS_DICT = load_words_with_ids(args.rahlfs)
    print(f"Loaded {len(RAHLFS_WORDS_DICT)} word IDs from Rahlfs")
    
    SWETE_WORDS_DICT = load_words_with_ids(args.swete)
    print(f"Loaded {len(SWETE_WORDS_DICT)} word IDs from Swete")
    
    # Derive normalized->original mappings once at startup
    print("Deriving normalized word sets...")
    RAHLFS_WORDS = derive_word_set(RAHLFS_WORDS_DICT)
    print(f"Derived {len(RAHLFS_WORDS)} unique words from Rahlfs")
    
    SWETE_WORDS = derive_word_set(SWETE_WORDS_DICT)
    print(f"Derived {len(SWETE_WORDS)} unique words from Swete")
    
    ACCEPTED_WORDS = load_accepted_words(args.accepted_words)
    if ACCEPTED_WORDS:
        print(f"Loaded {len(ACCEPTED_WORDS)} accepted words")
    
    ALREADY_EXAMINED = load_already_examined(args.already_examined)
    if ALREADY_EXAMINED:
        print(f"Loaded {len(ALREADY_EXAMINED)} already examined word changes")
    
    # Load versification data for verse-specific typo checking
    if check_typos:
        print("Loading versification for verse-specific typo checking...")
        RAHLFS_VERSE_MAP, RAHLFS_SORTED_VERSES = load_versification(args.rahlfs_versification)
        print(f"Loaded {len(RAHLFS_VERSE_MAP)} verses from Rahlfs versification")
        
        SWETE_VERSE_MAP, SWETE_SORTED_VERSES = load_versification(args.swete_versification)
        print(f"Loaded {len(SWETE_VERSE_MAP)} verses from Swete versification")
    
    process_bible_file(bible_path, output_path, check_typos)


if __name__ == '__main__':
    main()
