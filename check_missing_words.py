#!/usr/bin/env python3
"""
Script to check for Greek words in Bible-B9p01.tex that are not found in
rahlfs_words.csv or swete_words.csv files.
"""

import re
import unicodedata
import csv


def normalize_text(text):
    """Normalize Greek text using NFC normalization."""
    return unicodedata.normalize("NFC", text)


def strip_diacritics(text):
    """Remove diacritical marks and accents from Greek text."""
    # Normalize first
    text = normalize_text(text)
    # Remove combining characters (accents, breathing marks, etc.)
    stripped = ''.join(
        char for char in text 
        if unicodedata.category(char) != 'Mn'
    )
    return stripped


def load_word_set(filepath):
    """Load words from CSV file into a set with normalized and stripped versions."""
    words = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if len(row) >= 2:
                    word = normalize_text(row[1])
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


def is_word_in_sets(word, rahlfs_set, swete_set):
    """Check if word exists in either word set (case-insensitive, diacritic-stripped)."""
    normalized = strip_diacritics(word.lower())
    return normalized in rahlfs_set or normalized in swete_set


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
                        
                        missing_words.append({
                            'line_num': line_num,
                            'verse_ref': verse_ref,
                            'word': word,
                            'full_line': line
                        })
    
    # Write results to log file
    print(f"\nWriting results to {output_path}...")
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        # Write header
        writer.writerow(['Line Number', 'Verse Reference', 'Word', 'Full Line'])
        
        # Write data
        for entry in missing_words:
            writer.writerow([
                entry['line_num'],
                entry['verse_ref'],
                entry['word'],
                entry['full_line']
            ])
    
    print(f"\nComplete! Found {len(missing_words)} missing words.")
    print(f"Results saved to: {output_path}")


def main():
    """Main entry point."""
    # File paths
    bible_path = 'Bible-B9p01.tex'
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
