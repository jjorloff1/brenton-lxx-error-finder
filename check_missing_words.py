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


def derive_word_set(words_dict):
    """Derive normalized->original mapping from word_id dictionary.
    words_dict maps word_id -> {'normalized': str, 'original': str}.
    Returns dict mapping normalized -> original.
    """
    word_set = {}
    for word_data in words_dict.values():
        normalized = word_data['normalized']
        original = word_data['original']
        # Keep first occurrence (prefer earlier instances)
        if normalized not in word_set:
            word_set[normalized] = original
    return word_set


def load_words_with_ids(filepath):
    """Load words from CSV file with their word IDs for verse-specific lookups.
    Returns dict mapping word_id -> {'normalized': str, 'original': str}.
    """
    print(f"Opening file with word IDs: {filepath}")
    words_dict = {}  # word_id -> {'normalized': word, 'original': word}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            print(f"Successfully opened {filepath}")
            reader = csv.reader(f, delimiter='\t')
            row_count = 0
            for row in reader:
                row_count += 1
                if len(row) >= 2:
                    word_id = int(row[0])
                    word = normalize_text(row[-1])
                    normalized = strip_diacritics(word.lower())
                    words_dict[word_id] = {
                        'normalized': normalized,
                        'original': word.lower()
                    }
            print(f"Finished reading {filepath} ({row_count} rows, {len(words_dict)} word IDs loaded)")
    except Exception as e:
        print(f"Error loading {filepath} with IDs: {e}")
    return words_dict


def load_versification(filepath):
    """Load versification file mapping verses to word IDs."""
    print(f"Opening versification file: {filepath}")
    verse_map = {}  # verse_ref -> word_id
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            print(f"Successfully opened {filepath}")
            reader = csv.reader(f, delimiter='\t')
            row_count = 0
            for row in reader:
                row_count += 1
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
            print(f"Finished reading {filepath} ({row_count} rows, {len(verse_map)} verses loaded)")
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    
    # Pre-sort verses by word_id for efficient range lookup
    print(f"Sorting verses from {filepath}...")
    sorted_verses = sorted(verse_map.items(), key=lambda x: x[1])
    print(f"Finished sorting {len(sorted_verses)} verses")
    return verse_map, sorted_verses


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
    if best_ratio >= 0.85 and best_match_normalized:
        # Return original form with diacritics
        return word_dict[best_match_normalized], best_ratio
    else:
        # try adding ν if the word ends with a movable-nu-eligible ending
        # Movable ν can appear after: -ε, -ι
        if normalized.endswith('ε') or normalized.endswith('ι'):
            normalized_with_nu = normalized + 'ν'

            best_match_normalized, best_ratio = find_best_match(word_dict, normalized_with_nu, best_ratio)            
            
            # Check if adding ν improved the match to above threshold
            if best_ratio >= 0.85 and best_match_normalized:
                return word_dict[best_match_normalized], best_ratio
    
    return None, 0

def find_best_match(word_dict, normalized, current_best_ratio = 0):
    # Only check words of similar length (within 2 characters)
    target_len = len(normalized)
    
    best_match_normalized = None
    for candidate_normalized in word_dict.keys():
        if abs(len(candidate_normalized) - target_len) > 2:
            continue
            
        # Calculate similarity ratio
        ratio = SequenceMatcher(None, normalized, candidate_normalized).ratio()
        
        # If very similar (>0.8 similarity), it might be a typo
        if ratio > current_best_ratio:
            current_best_ratio = ratio
            best_match_normalized = candidate_normalized
    return best_match_normalized,current_best_ratio


def get_verse_words(verse_ref, verse_map, sorted_verses, words_dict):
    """Get all words for a specific verse using the versification mapping.
    words_dict maps word_id -> {'normalized': str, 'original': str}.
    Returns dict mapping normalized -> original for words in this verse.
    NOTE: This helper still takes parameters since it's used internally with different data sources.
    """
    verse_words = {}  # normalized -> original
    
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
            word_data = words_dict[word_id]
            verse_words[word_data['normalized']] = word_data['original']
    
    return verse_words


def get_area_words(verse_ref, verse_map, sorted_verses, words_dict, verse_range=2):
    """Get all words from surrounding verses (±verse_range verses).
    words_dict maps word_id -> {'normalized': str, 'original': str}.
    Returns dict mapping normalized -> original for words in this area.
    """
    area_words = {}  # normalized -> original
    
    # Find the current verse index in sorted list
    if verse_ref not in verse_map:
        return area_words
    
    current_idx = None
    for i, (v_ref, v_id) in enumerate(sorted_verses):
        if v_ref == verse_ref:
            current_idx = i
            break
    
    if current_idx is None:
        return area_words
    
    # Get range of verses (current ± verse_range)
    start_verse_idx = max(0, current_idx - verse_range)
    end_verse_idx = min(len(sorted_verses) - 1, current_idx + verse_range)
    
    # Get word IDs for the range
    start_word_id = sorted_verses[start_verse_idx][1]
    
    # Find the end word ID (start of next verse after range, minus 1)
    if end_verse_idx + 1 < len(sorted_verses):
        end_word_id = sorted_verses[end_verse_idx + 1][1] - 1
    else:
        end_word_id = max(words_dict.keys()) if words_dict else start_word_id
    
    # Extract all words in this ID range
    for word_id in range(start_word_id, end_word_id + 1):
        if word_id in words_dict:
            word_data = words_dict[word_id]
            area_words[word_data['normalized']] = word_data['original']
    
    return area_words


def is_likely_typo(word, brenton_book=None, brenton_ch=None, brenton_vs=None):
    """
    Check if word is likely a typo by finding very similar words.
    Uses global data structures (RAHLFS_WORDS_DICT, SWETE_WORDS_DICT, etc.).
    First checks verse-specific words, then area (±2 verses), then falls back to broader corpus.
    Returns (is_typo, closest_match, similarity_ratio, verse_match, area_match)
    """
    verse_match = False
    area_match = False
    
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
                # Check verse-specific words first (with movable nu handling)
                closest_r, ratio_r = find_closest_word(word, rahlfs_verse_words)
                closest_s, ratio_s = find_closest_word(word, swete_verse_words)
                
                best_ratio = max(ratio_r, ratio_s)
                best_match = closest_r if ratio_r > ratio_s else closest_s
                
                if best_ratio >= 0.85:
                    return True, best_match, best_ratio, True, False
            
            # If not found in exact verse, check surrounding area (±2 verses)
            rahlfs_area_words = get_area_words(rahlfs_ref, RAHLFS_VERSE_MAP, RAHLFS_SORTED_VERSES, RAHLFS_WORDS_DICT, verse_range=2)
            swete_area_words = get_area_words(swete_ref, SWETE_VERSE_MAP, SWETE_SORTED_VERSES, SWETE_WORDS_DICT, verse_range=2)
            
            if rahlfs_area_words or swete_area_words:
                # Check area words (with movable nu handling)
                closest_r, ratio_r = find_closest_word(word, rahlfs_area_words)
                closest_s, ratio_s = find_closest_word(word, swete_area_words)
                
                best_ratio = max(ratio_r, ratio_s)
                best_match = closest_r if ratio_r > ratio_s else closest_s
                
                if best_ratio >= 0.85:
                    return True, best_match, best_ratio, False, True
        except Exception:
            # If conversion or verse lookup fails, continue to broad search
            pass
    
    # Fall back to broad corpus search - use pre-derived global word sets
    closest_r, ratio_r = find_closest_word(word, RAHLFS_WORDS)
    closest_s, ratio_s = find_closest_word(word, SWETE_WORDS)
    
    best_ratio = max(ratio_r, ratio_s)
    best_match = closest_r if ratio_r > ratio_s else closest_s
    
    # If we found a very close match (85%+ similar), it's likely a typo
    if best_ratio >= 0.85:
        return True, best_match, best_ratio, False, False
    return False, None, 0, False, False


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


def process_bible_file(bible_path, output_path, check_typos=True):
    """Process the Bible file and log missing words.
    Uses global data structures (RAHLFS_WORDS_DICT, SWETE_WORDS_DICT, ACCEPTED_WORDS, etc.).
    """
    
    current_book = None
    current_chapter = None
    current_verse = None
    
    missing_words = []
    words_checked = 0
    typos_found = 0
    
    print("Processing Bible file...")
    if not check_typos:
        print("Typo checking disabled for faster processing.")
    
    print(f"Opening Bible file for reading: {bible_path}")
    with open(bible_path, 'r', encoding='utf-8') as f:
        print(f"Successfully opened {bible_path}")
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
                    # First check if word is in accepted words list (skip if accepted)
                    if ACCEPTED_WORDS:
                        normalized_word = strip_diacritics(word.lower())
                        if normalized_word in ACCEPTED_WORDS:
                            continue
                    
                    # Check if this word has already been examined in this verse
                    if ALREADY_EXAMINED and current_book and current_chapter and current_verse:
                        verse_ref = f"{current_book} {current_chapter}:{current_verse}"
                        normalized_word = strip_diacritics(word.lower())
                        key = (verse_ref, normalized_word)
                        if key in ALREADY_EXAMINED:
                            continue
                    
                    if not is_word_in_sets(word):
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
                            
                            is_typo, closest_match, similarity, verse_match, area_match = is_likely_typo(
                                word, current_book, current_chapter, current_verse
                            )
                            
                            if is_typo:
                                typos_found += 1
                        else:
                            is_typo, closest_match, similarity, verse_match, area_match = False, None, 0, False, False
                        
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
                            'verse_match': verse_match,
                            'area_match': area_match
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
            # Write header with all columns including verse match and area match
            writer.writerow(['Line Number', 'Verse Reference', 'Word', 'Is Name?', 'Is Number?', 
                            'Likely Typo?', 'Closest Match', 'Similarity', 'Verse Match?', 'Area Match?', 'Full Line'])
            
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
                    entry['full_line']
                ])
            print(f"Finished writing {len(missing_words)} rows to {typo_check_path}")
    
    # Create a filtered file with likely typos only
    if check_typos:
        filtered_path = output_path.replace('.tsv', '_likely_typos.tsv')
        likely_typos = [e for e in missing_words if e['is_typo'] and not e['is_name'] and not e['is_number']]
        
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
    
    print(f"\nComplete! Found {len(missing_words)} missing words.")
    if check_typos:
        print(f"  - Likely proper names: {sum(1 for e in missing_words if e['is_name'])}")
        print(f"  - Likely numbers: {sum(1 for e in missing_words if e['is_number'])}")
        print(f"  - Likely typos: {len(likely_typos)}")
        if likely_typos:
            verse_matches = sum(1 for e in likely_typos if e.get('verse_match', False))
            area_matches = sum(1 for e in likely_typos if e.get('area_match', False))
            corpus_matches = len(likely_typos) - verse_matches - area_matches
            print(f"    - Matched within verse: {verse_matches}")
            print(f"    - Matched within area (±2 verses): {area_matches}")
            print(f"    - Matched in broader corpus: {corpus_matches}")
    print(f"Results saved to: {output_path}")
    if check_typos:
        print(f"Full typo check results saved to: {typo_check_path}")
        print(f"Filtered typos saved to: {filtered_path}")


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
    parser.add_argument('--accepted-words', default='accepted_words.txt',
                        help='Path to accepted words file (default: accepted_words.txt)')
    parser.add_argument('--already-examined', default='word_corrections.tsv',
                        help='Path to already examined word changes file (default: word_corrections.tsv)')
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
