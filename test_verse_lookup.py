#!/usr/bin/env python3
"""Quick test of verse-specific word lookup."""

import csv
import sys

def load_words_with_ids(filepath, max_lines=1000):
    """Load words from CSV file with their word IDs (limited for testing)."""
    words_dict = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            for i, row in enumerate(reader):
                if i >= max_lines:
                    break
                if len(row) >= 2:
                    word_id = int(row[0])
                    word = row[-1]
                    words_dict[word_id] = word
    except Exception as e:
        print(f"Error loading {filepath} with IDs: {e}")
    return words_dict


def load_versification(filepath, max_lines=100):
    """Load versification file mapping verses to word IDs (limited for testing)."""
    verse_map = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            for i, row in enumerate(reader):
                if i >= max_lines:
                    break
                if len(row) >= 2:
                    # Detect format by checking if first column is numeric
                    try:
                        word_id = int(row[0])
                        verse_ref = row[1]
                    except ValueError:
                        verse_ref = row[0]
                        word_id = int(row[1])
                    verse_map[verse_ref] = word_id
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return verse_map


def get_verse_words(verse_ref, verse_map, words_dict):
    """Get all words for a specific verse."""
    verse_words = []
    
    if verse_ref not in verse_map:
        return verse_words
    
    start_id = verse_map[verse_ref]
    
    # Find the next verse to get end boundary
    sorted_verses = sorted(verse_map.items(), key=lambda x: x[1])
    current_idx = None
    for i, (v_ref, v_id) in enumerate(sorted_verses):
        if v_ref == verse_ref:
            current_idx = i
            break
    
    if current_idx is not None and current_idx + 1 < len(sorted_verses):
        end_id = sorted_verses[current_idx + 1][1] - 1
    else:
        end_id = max(words_dict.keys()) if words_dict else start_id
    
    # Extract words in this ID range
    for word_id in range(start_id, end_id + 1):
        if word_id in words_dict:
            verse_words.append(words_dict[word_id])
    
    return verse_words


if __name__ == '__main__':
    print("Testing Rahlfs...")
    rahlfs_words = load_words_with_ids('rahlfs_words.csv', max_lines=300)
    print(f"Loaded {len(rahlfs_words)} words")
    
    rahlfs_verses = load_versification('rahlfs_versification.csv', max_lines=20)
    print(f"Loaded {len(rahlfs_verses)} verses")
    print("Verses:", list(rahlfs_verses.keys())[:5])
    
    # Test getting words for Gen.1.1
    verse_ref = "Gen.1.1"
    words = get_verse_words(verse_ref, rahlfs_verses, rahlfs_words)
    print(f"\nWords in {verse_ref}: {words}")
    
    print("\n" + "="*50)
    print("Testing Swete...")
    swete_words = load_words_with_ids('swete_words.csv', max_lines=300)
    print(f"Loaded {len(swete_words)} words")
    
    swete_verses = load_versification('swete_versification.csv', max_lines=20)
    print(f"Loaded {len(swete_verses)} verses")
    print("Verses:", list(swete_verses.keys())[:5])
    
    # Test getting words for Gen.1:1
    verse_ref = "Gen.1:1"
    words = get_verse_words(verse_ref, swete_verses, swete_words)
    print(f"\nWords in {verse_ref}: {words}")
