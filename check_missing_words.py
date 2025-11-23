#!/usr/bin/env python3
"""
Script to check for Greek words in Brenton.tex that are not found in
rahlfs_words.csv or swete_words.csv files.
"""

import re
import unicodedata
import csv
from difflib import SequenceMatcher


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


def is_likely_typo(word, rahlfs_set, swete_set):
    """Check if word is likely a typo by finding very similar words in the sets."""
    closest_r, ratio_r = find_closest_word(word, rahlfs_set)
    closest_s, ratio_s = find_closest_word(word, swete_set)
    
    best_ratio = max(ratio_r, ratio_s)
    best_match = closest_r if ratio_r > ratio_s else closest_s
    
    # If we found a very close match (85%+ similar), it's likely a typo
    if best_ratio >= 0.85:
        return True, best_match, best_ratio
    return False, None, 0


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


def process_bible_file(bible_path, rahlfs_set, swete_set, output_path):
    """Process the Bible file and log missing words."""
    
    current_book = None
    current_chapter = None
    current_verse = None
    
    missing_words = []
    
    print("Processing Bible file...")
    
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
                        is_name = is_likely_proper_name(word)
                        
                        # Check if likely number word
                        is_number = is_likely_number_word(word)
                        
                        # Check if likely typo
                        is_typo, closest_match, similarity = is_likely_typo(word, rahlfs_set, swete_set)
                        
                        missing_words.append({
                            'line_num': line_num,
                            'verse_ref': verse_ref,
                            'word': word,
                            'full_line': line,
                            'is_name': is_name,
                            'is_number': is_number,
                            'is_typo': is_typo,
                            'closest_match': closest_match if closest_match else '',
                            'similarity': f"{similarity:.2f}" if similarity > 0 else ''
                        })
    
    # Write results to log file
    print(f"\nWriting results to {output_path}...")
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        # Write header
        writer.writerow(['Line Number', 'Verse Reference', 'Word', 'Is Name?', 'Is Number?', 
                        'Likely Typo?', 'Closest Match', 'Similarity', 'Full Line'])
        
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
                entry['full_line']
            ])
    
    # Create a filtered file with likely typos only
    filtered_path = output_path.replace('.tsv', '_likely_typos.tsv')
    likely_typos = [e for e in missing_words if e['is_typo'] and not e['is_name'] and not e['is_number']]
    
    print(f"Writing likely typos to {filtered_path}...")
    with open(filtered_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        # Write header
        writer.writerow(['Line Number', 'Verse Reference', 'Word', 'Closest Match', 'Similarity', 'Full Line'])
        
        # Write data
        for entry in likely_typos:
            writer.writerow([
                entry['line_num'],
                entry['verse_ref'],
                entry['word'],
                entry['closest_match'],
                entry['similarity'],
                entry['full_line']
            ])
    
    print(f"\nComplete! Found {len(missing_words)} missing words.")
    print(f"  - Likely proper names: {sum(1 for e in missing_words if e['is_name'])}")
    print(f"  - Likely numbers: {sum(1 for e in missing_words if e['is_number'])}")
    print(f"  - Likely typos: {len(likely_typos)}")
    print(f"Results saved to: {output_path}")
    print(f"Filtered typos saved to: {filtered_path}")


def main():
    """Main entry point."""
    # File paths
    bible_path = 'Brenton.tex'
    rahlfs_path = 'rahlfs_words.csv'
    swete_path = 'swete_words.csv'
    output_path = 'missing_words.tsv'
    
    print("Loading word sets...")
    rahlfs_set = load_word_set(rahlfs_path)
    print(f"Loaded {len(rahlfs_set)} words from Rahlfs")
    
    swete_set = load_word_set(swete_path)
    print(f"Loaded {len(swete_set)} words from Swete")
    
    process_bible_file(bible_path, rahlfs_set, swete_set, output_path)


if __name__ == '__main__':
    main()
