#!/usr/bin/env python3
"""
Script to check for Greek words in Brenton.tex that are not found in
rahlfs_words.csv or swete_words.csv files.
"""

import re
import unicodedata
import csv
import argparse
from difflib import SequenceMatcher
from book_code_mappings import (
    convert_brenton_reference_to_rahlfs,
    convert_brenton_reference_to_swete
)


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


def load_word_set(filepath):
    """Load words from CSV file into a set with normalized and stripped versions."""
    words = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if len(row) >= 2:
                    # Rahlfs has 3 columns (num, num, word), Swete has 2 (num, word)
                    # Use the last column which is always the word
                    word = normalize_text(row[-1])
                    # Store both case-insensitive and diacritic-stripped version
                    normalized = strip_diacritics(word.lower())
                    words.add(normalized)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return words


def load_words_with_ids(filepath):
    """Load words from CSV file with their word IDs for verse-specific lookups."""
    words_dict = {}  # word_id -> normalized_word
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if len(row) >= 2:
                    word_id = int(row[0])
                    word = normalize_text(row[-1])
                    normalized = strip_diacritics(word.lower())
                    words_dict[word_id] = normalized
    except Exception as e:
        print(f"Error loading {filepath} with IDs: {e}")
    return words_dict


def load_versification(filepath):
    """Load versification file mapping verses to word IDs."""
    verse_map = {}  # verse_ref -> word_id
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if len(row) >= 2:
                    # Rahlfs: verse_ref, word_id
                    # Swete: word_id, verse_ref
                    # Detect format by checking if first column is numeric
                    try:
                        word_id = int(row[0])
                        verse_ref = row[1]
                    except ValueError:
                        # First column is verse ref, second is word_id
                        verse_ref = row[0]
                        word_id = int(row[1])
                    verse_map[verse_ref] = word_id
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    
    # Pre-sort verses by word_id for efficient range lookup
    sorted_verses = sorted(verse_map.items(), key=lambda x: x[1])
    return verse_map, sorted_verses


def extract_greek_words(line):
    """Extract Greek words from a line, excluding LaTeX commands."""
    # Remove LaTeX commands and their contents
    line = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', line)
    line = re.sub(r'\\[a-zA-Z]+', '', line)
    
    # Match Greek words (unicode Greek range)
    # Greek range: \u0370-\u03FF (basic Greek), \u1F00-\u1FFF (extended Greek)
    greek_pattern = r'[\u0370-\u03FF\u1F00-\u1FFF]+'
    words = re.findall(greek_pattern, line)
    
    return [normalize_text(word) for word in words]


def is_likely_proper_name(word):
    """Check if a word is likely a proper name (starts with capital)."""
    # After normalization, check if the first character is uppercase
    return len(word) > 0 and word[0].isupper()


def is_likely_number_word(word):
    """Check if word appears to be a number/numeral."""
    # Greek number words often contain these patterns
    number_patterns = [
        'ἑκατό', 'χίλι', 'μύρι',  # hundred, thousand, myriad
        'δέκα', 'εἴκοσι', 'τριάκοντα', 'τεσσαράκοντα', 'πεντήκοντα',
        'ἑξήκοντα', 'ἑβδομήκοντα', 'ὀγδοήκοντα', 'ἐνενήκοντα', 'ἐννενήκοντα', 'ἐννεήκοντα',
        'πρῶτο', 'δεύτερο', 'τρίτο', 'τέταρτο', 'πέμπτο',
        'διακόσι', 'τριακόσι', 'τετρακόσι', 'πεντακόσι', 'ἑξακόσι', 'ἑπτακόσι', 'ὀκτακόσι', 'ἐννακόσι'
    ]
    word_lower = word.lower()
    word_stripped = strip_diacritics(word_lower)
    
    for pattern in number_patterns:
        pattern_stripped = strip_diacritics(pattern.lower())
        if pattern_stripped in word_stripped:
            return True
    return False


def find_closest_word(word, word_set, max_distance=2):
    """Find the closest matching word in the set within max_distance edits."""
    normalized = strip_diacritics(word.lower())
    best_match = None
    best_ratio = 0
    
    # Only check words of similar length (within 2 characters)
    target_len = len(normalized)
    
    for candidate in word_set:
        if abs(len(candidate) - target_len) > 2:
            continue
            
        # Calculate similarity ratio
        ratio = SequenceMatcher(None, normalized, candidate).ratio()
        
        # If very similar (>0.8 similarity), it might be a typo
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = candidate
    
    # Return match only if it's very close (likely a typo)
    if best_ratio >= 0.85:
        return best_match, best_ratio
    return None, 0


def get_verse_words(verse_ref, verse_map, sorted_verses, words_dict):
    """Get all words for a specific verse using the versification mapping."""
    verse_words = set()
    
    # Find start word ID for this verse
    if verse_ref not in verse_map:
        return verse_words
    
    start_id = verse_map[verse_ref]
    
    # Find the next verse to get end boundary using pre-sorted list
    current_idx = None
    for i, (v_ref, v_id) in enumerate(sorted_verses):
        if v_ref == verse_ref:
            current_idx = i
            break
    
    # Determine end ID
    if current_idx is not None and current_idx + 1 < len(sorted_verses):
        end_id = sorted_verses[current_idx + 1][1] - 1
    else:
        # Last verse - use maximum word ID
        end_id = max(words_dict.keys()) if words_dict else start_id
    
    # Extract words in this ID range
    for word_id in range(start_id, end_id + 1):
        if word_id in words_dict:
            verse_words.add(words_dict[word_id])
    
    return verse_words


def is_likely_typo(word, rahlfs_set, swete_set, 
                   brenton_book=None, brenton_ch=None, brenton_vs=None,
                   rahlfs_verse_map=None, swete_verse_map=None,
                   rahlfs_sorted_verses=None, swete_sorted_verses=None,
                   rahlfs_words_dict=None, swete_words_dict=None):
    """
    Check if word is likely a typo by finding very similar words in the sets.
    First checks verse-specific words if verse context provided, then falls back to broader corpus.
    Returns (is_typo, closest_match, similarity_ratio, verse_match)
    """
    verse_match = False
    
    # First try verse-specific search if we have the necessary data
    if all([brenton_book, brenton_ch, brenton_vs, rahlfs_verse_map, swete_verse_map, 
            rahlfs_sorted_verses, swete_sorted_verses,
            rahlfs_words_dict, swete_words_dict]):
        try:
            rahlfs_ref = convert_brenton_reference_to_rahlfs(brenton_book, brenton_ch, brenton_vs)
            swete_ref = convert_brenton_reference_to_swete(brenton_book, brenton_ch, brenton_vs)
            
            rahlfs_verse_words = get_verse_words(rahlfs_ref, rahlfs_verse_map, rahlfs_sorted_verses, rahlfs_words_dict)
            swete_verse_words = get_verse_words(swete_ref, swete_verse_map, swete_sorted_verses, swete_words_dict)
            
            if rahlfs_verse_words or swete_verse_words:
                # Check verse-specific words first
                closest_r, ratio_r = find_closest_word(word, rahlfs_verse_words)
                closest_s, ratio_s = find_closest_word(word, swete_verse_words)
                
                best_ratio = max(ratio_r, ratio_s)
                best_match = closest_r if ratio_r > ratio_s else closest_s
                
                if best_ratio >= 0.85:
                    return True, best_match, best_ratio, True
        except Exception:
            # If conversion or verse lookup fails, continue to broad search
            pass
    
    # Fall back to broad corpus search
    closest_r, ratio_r = find_closest_word(word, rahlfs_set)
    closest_s, ratio_s = find_closest_word(word, swete_set)
    
    best_ratio = max(ratio_r, ratio_s)
    best_match = closest_r if ratio_r > ratio_s else closest_s
    
    # If we found a very close match (85%+ similar), it's likely a typo
    if best_ratio >= 0.85:
        return True, best_match, best_ratio, False
    return False, None, 0, False


def is_word_in_sets(word, rahlfs_set, swete_set):
    """Check if word exists in either word set (case-insensitive, diacritic-stripped)."""
    normalized = strip_diacritics(word.lower())
    
    # First, try the word as-is
    if normalized in rahlfs_set or normalized in swete_set:
        return True
    
    # Second, try with movable ν added at the end
    # This handles cases where Brenton drops the movable nu
    normalized_with_nu = normalized + 'ν'
    if normalized_with_nu in rahlfs_set or normalized_with_nu in swete_set:
        return True
    
    return False
    """Check if word exists in either word set (case-insensitive, diacritic-stripped)."""
    normalized = strip_diacritics(word.lower())
    
    # First, try the word as-is
    if normalized in rahlfs_set or normalized in swete_set:
        return True
    
    # Second, try with movable ν added at the end
    # This handles cases where Brenton drops the movable nu
    normalized_with_nu = normalized + 'ν'
    if normalized_with_nu in rahlfs_set or normalized_with_nu in swete_set:
        return True
    
    return False


def extract_book_name(line):
    """Extract book name from \\biblebook{...} command."""
    match = re.search(r'\\biblebook\{([^}]+)\}', line)
    if match:
        return normalize_text(match.group(1))
    return None


def extract_chapter_number(line):
    """Extract chapter number from \\ch{...} or \\lettrine lines."""
    # Check for regular chapter command
    match = re.search(r'\\ch\{(\d+)\}', line)
    if match:
        return int(match.group(1))
    
    # Check for lettrine (first chapter, starts with chapter 1)
    if r'\lettrine' in line:
        return 1
    
    return None


def extract_verse_number(line):
    """Extract verse number from \\vs{...} command."""
    match = re.search(r'\\vs\{(\d+)\}', line)
    if match:
        return int(match.group(1))
    return None


def process_bible_file(bible_path, rahlfs_set, swete_set, output_path, check_typos=True,
                       rahlfs_verse_map=None, swete_verse_map=None,
                       rahlfs_sorted_verses=None, swete_sorted_verses=None,
                       rahlfs_words_dict=None, swete_words_dict=None):
    """Process the Bible file and log missing words."""
    
    current_book = None
    current_chapter = None
    current_verse = None
    
    missing_words = []
    words_checked = 0
    typos_found = 0
    
    print("Processing Bible file...")
    if not check_typos:
        print("Typo checking disabled for faster processing.")
    
    with open(bible_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Track book name
            book = extract_book_name(line)
            if book:
                current_book = book
                current_chapter = None
                current_verse = None
                print(f"Found book: {current_book}")
                continue
            
            # Track chapter number
            chapter = extract_chapter_number(line)
            if chapter:
                current_chapter = chapter
                # First verse is implied after chapter declaration
                current_verse = 1
            
            # Track verse number
            verse = extract_verse_number(line)
            if verse:
                current_verse = verse
            
            # Extract and check Greek words
            greek_words = extract_greek_words(line)
            if greek_words:
                for word in greek_words:
                    if not is_word_in_sets(word, rahlfs_set, swete_set):
                        # Build verse reference
                        verse_ref = "Unknown"
                        if current_book and current_chapter and current_verse:
                            verse_ref = f"{current_book} {current_chapter}:{current_verse}"
                        
                        # Check if likely proper name
                        is_name = is_likely_proper_name(word) if check_typos else False
                        
                        # Check if likely number word
                        is_number = is_likely_number_word(word) if check_typos else False
                        
                        # Check if likely typo (with optional verse-specific checking)
                        if check_typos:
                            words_checked += 1
                            if words_checked % 100 == 0:
                                print(f"  Checked {words_checked} words, found {typos_found} potential typos so far... (Current: {verse_ref})")
                            
                            is_typo, closest_match, similarity, verse_match = is_likely_typo(
                                word, rahlfs_set, swete_set,
                                current_book, current_chapter, current_verse,
                                rahlfs_verse_map, swete_verse_map,
                                rahlfs_sorted_verses, swete_sorted_verses,
                                rahlfs_words_dict, swete_words_dict
                            )
                            
                            if is_typo:
                                typos_found += 1
                        else:
                            is_typo, closest_match, similarity, verse_match = False, None, 0, False
                        
                        missing_words.append({
                            'line_num': line_num,
                            'verse_ref': verse_ref,
                            'word': word,
                            'full_line': line,
                            'is_name': is_name,
                            'is_number': is_number,
                            'is_typo': is_typo,
                            'closest_match': closest_match if closest_match else '',
                            'similarity': f"{similarity:.2f}" if similarity > 0 else '',
                            'verse_match': verse_match
                        })
    
    # Write results to log file
    print(f"\nWriting results to {output_path}...")
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
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
    
    # Write full typo check results if enabled
    if check_typos:
        typo_check_path = output_path.replace('.tsv', '_typo_check.tsv')
        print(f"Writing full typo check results to {typo_check_path}...")
        with open(typo_check_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            # Write header with all columns including verse match
            writer.writerow(['Line Number', 'Verse Reference', 'Word', 'Is Name?', 'Is Number?', 
                            'Likely Typo?', 'Closest Match', 'Similarity', 'Verse Match?', 'Full Line'])
            
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
                    entry['full_line']
                ])
    
    # Create a filtered file with likely typos only
    if check_typos:
        filtered_path = output_path.replace('.tsv', '_likely_typos.tsv')
        likely_typos = [e for e in missing_words if e['is_typo'] and not e['is_name'] and not e['is_number']]
        
        print(f"Writing likely typos to {filtered_path}...")
        with open(filtered_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            # Write header with verse match column
            writer.writerow(['Line Number', 'Verse Reference', 'Word', 'Closest Match', 'Similarity', 'Verse Match?', 'Full Line'])
            
            # Write data
            for entry in likely_typos:
                writer.writerow([
                    entry['line_num'],
                    entry['verse_ref'],
                    entry['word'],
                    entry['closest_match'],
                    entry['similarity'],
                    'Yes' if entry.get('verse_match', False) else 'No',
                    entry['full_line']
                ])
    
    print(f"\nComplete! Found {len(missing_words)} missing words.")
    if check_typos:
        print(f"  - Likely proper names: {sum(1 for e in missing_words if e['is_name'])}")
        print(f"  - Likely numbers: {sum(1 for e in missing_words if e['is_number'])}")
        print(f"  - Likely typos: {len(likely_typos)}")
        if likely_typos:
            verse_matches = sum(1 for e in likely_typos if e.get('verse_match', False))
            print(f"    - Matched within verse: {verse_matches}")
            print(f"    - Matched in broader corpus: {len(likely_typos) - verse_matches}")
    print(f"Results saved to: {output_path}")
    if check_typos:
        print(f"Full typo check results saved to: {typo_check_path}")
        print(f"Filtered typos saved to: {filtered_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Check for Greek words in Bible file that are not found in reference word lists.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with typo checking (default):
  python check_missing_words.py
  
  # Run without typo checking (faster):
  python check_missing_words.py --no-typo-check
  
  # Specify custom input files:
  python check_missing_words.py --bible MyBible.tex --rahlfs rahlfs.csv
        """
    )
    
    parser.add_argument('--bible', default='Brenton.tex',
                        help='Path to Bible .tex file (default: Brenton.tex)')
    parser.add_argument('--rahlfs', default='rahlfs_words.csv',
                        help='Path to Rahlfs words CSV file (default: rahlfs_words.csv)')
    parser.add_argument('--swete', default='swete_words.csv',
                        help='Path to Swete words CSV file (default: swete_words.csv)')
    parser.add_argument('--rahlfs-versification', default='rahlfs_versification.csv',
                        help='Path to Rahlfs versification CSV file (default: rahlfs_versification.csv)')
    parser.add_argument('--swete-versification', default='swete_versification.csv',
                        help='Path to Swete versification CSV file (default: swete_versification.csv)')
    parser.add_argument('--output', default='missing_words.tsv',
                        help='Path to output TSV file (default: missing_words.tsv)')
    parser.add_argument('--no-typo-check', action='store_true',
                        help='Disable typo checking for faster processing')
    
    args = parser.parse_args()
    
    # File paths
    bible_path = args.bible
    rahlfs_path = args.rahlfs
    swete_path = args.swete
    rahlfs_vers_path = args.rahlfs_versification
    swete_vers_path = args.swete_versification
    output_path = args.output
    check_typos = not args.no_typo_check
    
    print("Loading word sets...")
    rahlfs_set = load_word_set(rahlfs_path)
    print(f"Loaded {len(rahlfs_set)} words from Rahlfs")
    
    swete_set = load_word_set(swete_path)
    print(f"Loaded {len(swete_set)} words from Swete")
    
    # Load additional data for verse-specific typo checking
    rahlfs_words_dict = None
    swete_words_dict = None
    rahlfs_verse_map = None
    swete_verse_map = None
    rahlfs_sorted_verses = None
    swete_sorted_verses = None
    
    if check_typos:
        print("Loading word IDs and versification for verse-specific typo checking...")
        rahlfs_words_dict = load_words_with_ids(rahlfs_path)
        print(f"Loaded {len(rahlfs_words_dict)} word IDs from Rahlfs")
        
        swete_words_dict = load_words_with_ids(swete_path)
        print(f"Loaded {len(swete_words_dict)} word IDs from Swete")
        
        rahlfs_verse_map, rahlfs_sorted_verses = load_versification(rahlfs_vers_path)
        print(f"Loaded {len(rahlfs_verse_map)} verses from Rahlfs versification")
        
        swete_verse_map, swete_sorted_verses = load_versification(swete_vers_path)
        print(f"Loaded {len(swete_verse_map)} verses from Swete versification")
    
    process_bible_file(bible_path, rahlfs_set, swete_set, output_path, check_typos,
                      rahlfs_verse_map, swete_verse_map,
                      rahlfs_sorted_verses, swete_sorted_verses,
                      rahlfs_words_dict, swete_words_dict)


if __name__ == '__main__':
    main()
