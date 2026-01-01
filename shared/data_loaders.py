"""
Data loading utilities for the Brenton LXX Error Finder.

Provides functions for loading:
- Word lists with IDs from CSV files
- Versification mappings
- Verse-specific word lookups
"""

import csv
from .greek_utils import normalize_text, strip_diacritics


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
    """Load versification file mapping verses to word IDs.
    Returns (verse_map, sorted_verses) where:
    - verse_map: dict mapping verse_ref -> word_id
    - sorted_verses: list of (verse_ref, word_id) tuples sorted by word_id
    """
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


def get_words_by_id_range(start_word_id, end_word_id, words_dict):
    """Extract words in a given word ID range, including compound combinations.

    Args:
        start_word_id: Starting word ID (inclusive)
        end_word_id: Ending word ID (inclusive)
        words_dict: Dictionary mapping word_id -> {'normalized': str, 'original': str}

    Returns:
        Dictionary mapping normalized -> original for words in this range,
        including compound combinations of consecutive words.
    """
    result_words = {}  # normalized -> original
    words_in_order = []

    # Extract words in this ID range and track order
    for word_id in range(start_word_id, end_word_id + 1):
        if word_id in words_dict:
            word_data = words_dict[word_id]
            result_words[word_data['normalized']] = word_data['original']
            words_in_order.append(word_data)

    # Add compound combinations of consecutive words
    for i in range(len(words_in_order) - 1):
        word1 = words_in_order[i]
        word2 = words_in_order[i + 1]
        combined_normalized = word1['normalized'] + word2['normalized']
        # Preserve space in the original form
        combined_original = word1['original'] + ' ' + word2['original']
        result_words[combined_normalized] = combined_original

    return result_words


def get_verse_words(verse_ref, verse_map, sorted_verses, words_dict):
    """Get all words for a specific verse using the versification mapping.
    words_dict maps word_id -> {'normalized': str, 'original': str}.
    Returns dict mapping normalized -> original for words in this verse.
    Also includes compound combinations of consecutive words (e.g., word1+word2).
    """
    # Find start word ID for this verse
    if verse_ref not in verse_map:
        return {}

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

    return get_words_by_id_range(start_id, end_id, words_dict)


def get_area_words(verse_ref, verse_map, sorted_verses, words_dict, verse_range=20):
    """Get all words from surrounding verses (±verse_range verses).
    words_dict maps word_id -> {'normalized': str, 'original': str}.
    Returns dict mapping normalized -> original for words in this area.
    Also includes compound combinations of consecutive words (e.g., word1+word2).
    """
    # Find the current verse index in sorted list
    if verse_ref not in verse_map:
        return {}

    current_idx = None
    for i, (v_ref, v_id) in enumerate(sorted_verses):
        if v_ref == verse_ref:
            current_idx = i
            break

    if current_idx is None:
        return {}

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

    return get_words_by_id_range(start_word_id, end_word_id, words_dict)
