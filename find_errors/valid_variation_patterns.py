#!/usr/bin/env python3
"""
Valid Greek spelling variation patterns for Brenton LXX.
These are legitimate textual/dialectal variants that should NOT be flagged as errors.
"""

import unicodedata
from itertools import product

def strip_accents(text):
    """Remove Greek accents for pattern matching."""
    # Normalize to NFD (decomposed form) so accents are separate
    nfd = unicodedata.normalize('NFD', text)
    # Filter out combining marks (accents)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')


def generate_positional_variations(text, pattern1, pattern2):
    """
    Generate variations where each occurrence of pattern1 can independently
    be replaced with pattern2 or left as is.
    
    For example, with 'ειει' and pattern ει→ι, generates:
    - ειει (no change)
    - ιει (first changed)
    - ειι (second changed)
    - ιι (both changed)
    """
    if pattern1 not in text:
        return {text}
    
    # Find all occurrences
    positions = []
    start = 0
    while True:
        pos = text.find(pattern1, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1  # Allow overlapping matches
    
    if not positions:
        return {text}
    
    # Generate all combinations (2^n where n is number of occurrences)
    variations = set()
    for combo in product([False, True], repeat=len(positions)):
        # Build the variation
        result = list(text)
        offset = 0
        for pos, should_replace in zip(positions, combo):
            if should_replace:
                # Replace pattern1 with pattern2 at this position
                adjusted_pos = pos + offset
                result[adjusted_pos:adjusted_pos+len(pattern1)] = list(pattern2)
                offset += len(pattern2) - len(pattern1)
        
        variations.add(''.join(result))
    
    return variations


def apply_pattern_bidirectional(text, pattern1, pattern2):
    """Apply pattern replacement in both directions."""
    results = {text}
    if pattern1 in text:
        results.add(text.replace(pattern1, pattern2))
    if pattern2 in text:
        results.add(text.replace(pattern2, pattern1))
    return results


def check_pattern_match(word1_norm, word2_norm, patterns):
    """
    Check if two normalized words differ only by one of the given patterns.
    Patterns can be tuples of (pattern1, pattern2) or (pattern1, pattern2, pattern3).
    """
    for pattern_group in patterns:
        if len(pattern_group) == 2:
            p1, p2 = pattern_group
            if (p1 in word1_norm or p2 in word1_norm) and (p1 in word2_norm or p2 in word2_norm):
                if word1_norm.replace(p1, p2) == word2_norm or word2_norm.replace(p2, p1) == word1_norm:
                    return True
        elif len(pattern_group) == 3:
            p1, p2, p3 = pattern_group
            # Check all pairwise combinations
            for pa, pb in [(p1, p2), (p1, p3), (p2, p3)]:
                if (pa in word1_norm or pb in word1_norm) and (pa in word2_norm or pb in word2_norm):
                    if word1_norm.replace(pa, pb) == word2_norm or word2_norm.replace(pb, pa) == word1_norm:
                        return True
    return False


# ============================================================================
# ALL VARIATION PATTERNS - Organized by Category
# ============================================================================

# Dictionary mapping pattern types to their pattern lists
VARIATION_PATTERNS = {
    'lambda_future': [
        ('ληψ', 'λημψ'),      # Future stems: λήψομαι ↔ λήμψομαι
        ('ληπ', 'λημπ'),      # Present/aorist stems: ἐπίληπτον ↔ ἐπίλημπτον
        ('ληφ', 'λημφ'),      # Aorist passive stems: ληφθῆναι ↔ λημφθῆναι
    ],
    
    
    'destruction': [
        ('ολοθρ', 'ολεθρ'), ('ολοθρευ', 'ολεθρευ'), ('ὠλόθρευ', 'ὠλέθρευ'),
        ('ξολοθρ', 'ξολεθρ'), ('ξωλοθρ', 'ξωλεθρ'),
    ],
    
    'generation': [
        ('γεννη', 'γενη')
    ],
    
    'circumcision': [
        ('τεμ', 'τεμν')
    ],
    
    'vowel_contraction': [
        ('εω', 'ω'), ('οε', 'ου'), ('αε', 'α'), ('αο', 'ω'), ('εε', 'ει'), ('η', 'ει'),
    ],
    
    'diphthong': [
        ('ει', 'ι'), ('οι', 'υ'), ('αι', 'ε'),
    ],
    
    'ablaut': [
        ('ε', 'η'), ('ο', 'ω'), ('α', 'η'),
    ],
    
    'aorist_vowel': [
        ('φειλ', 'φηλ'), ('ειλ', 'ηλ'),
    ],
    
    'aorist_consonant': [
        ('θη', 'ση'),
    ],
    
    'consonant_cluster': [
        ('π', 'μπ'), ('β', 'μβ'),
    ],
    
    'compound_prefix': [
        ('προσ', 'προ'), ('κατα', 'κατ', 'καθ'), ('ἀπο', 'ἀπ', 'ἀφ'),
        ('ἐπι', 'ἐπ', 'ἐφ'), ('συν', 'συμ'), ('συν', 'συλ'),
        ('συν', 'συγ'), ('συν', 'συσ'),
    ],
    
    'dialectal': [
        ('ρρ', 'ρ'), ('λλ', 'λ'), ('σσ', 'σ'), ('ττ', 'τ'), ('ττ', 'σσ'), ('ν', 'νν'),
    ],
    
    'participle': [
        ('ουσ', 'οντ'), ('ων', 'οντ'), ('ομεν', 'ωμεν'),
    ],
}

# Specific word variants (not pattern-based)
SPECIFIC_WORD_VARIANTS = {
    'δίδραγμον': ['διδραχμον', 'δίδραχμον'],
    'ψέλλιον': ['ψέλιον', 'ψελλιον'],
    'χιμάρρο': ['χειμάρρο', 'χειμάῤῥο', 'χιμάῤῥο'],
    'πρώϊμον': ['πρόϊμον', 'πρόιμον', 'πρωϊμον'],
    'πελακάν': ['πελεκάν'],
    'βδέλυμα': ['βδέλυγμα'],
    'τροφοφορ': ['τροπο φορ'],
    'ἐξεναντί': ['ἐναντί'],
}

# Pattern type groupings for semantic organization
PATTERN_GROUPS = {
    'lambda_future': ['lambda_future'],
    'destruction_verb': ['destruction'],
    'generation_word': ['generation'],
    'circumcision_verb': ['circumcision'],
    'vowel_variation': ['vowel_contraction', 'diphthong', 'ablaut'],
    'aorist_variation': ['aorist_vowel', 'aorist_consonant', 'consonant_cluster'],
    'dialectal_consonant': ['dialectal'],
    'compound_variation': ['compound_prefix'],
    'participle_variation': ['participle'],
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def has_lambda_future_variation(word1, word2):
    """Check if two words differ only in lambda future stem."""
    word1_norm = strip_accents(word1.lower())
    word2_norm = strip_accents(word2.lower())
    
    for pattern_type in PATTERN_GROUPS['lambda_future']:
        if check_pattern_match(word1_norm, word2_norm, VARIATION_PATTERNS[pattern_type]):
            return True
    return False


def has_destruction_verb_variation(word1, word2):
    """Check if two words differ only in destruction verb stem."""
    word1_norm = strip_accents(word1.lower())
    word2_norm = strip_accents(word2.lower())
    return check_pattern_match(word1_norm, word2_norm, VARIATION_PATTERNS['destruction'])


def has_generation_variation(word1, word2):
    """Check if two words differ only in generation/produce word stem."""
    word1_norm = strip_accents(word1.lower())
    word2_norm = strip_accents(word2.lower())
    return check_pattern_match(word1_norm, word2_norm, VARIATION_PATTERNS['generation'])


def is_likely_legitimate_variation(word1, word2):
    """
    Check if two words represent a likely legitimate spelling variation
    rather than a transcription error.
    
    Returns (is_variation, variation_type) tuple.
    """
    word1_norm = strip_accents(word1.lower())
    word2_norm = strip_accents(word2.lower())
    
    # Check each pattern group
    pattern_type_map = {
        'lambda_future': 'lambda_future',
        'destruction': 'destruction_verb',
        'generation': 'generation_word',
        'circumcision': 'circumcision_verb',
        'vowel_contraction': 'vowel_contraction',
        'diphthong': 'diphthong_variation',
        'ablaut': 'ablaut',
        'aorist_vowel': 'aorist_vowel',
        'aorist_consonant': 'aorist_consonant',
        'dialectal': 'dialectal_consonant',
        'consonant_cluster': 'consonant_cluster',
        'compound_prefix': 'compound_prefix',
        'participle': 'participle',
    }
    
    for pattern_key, return_type in pattern_type_map.items():
        if check_pattern_match(word1_norm, word2_norm, VARIATION_PATTERNS[pattern_key]):
            return (True, return_type)
    
    # Generate all variations of word1 and see if word2 is among them
    # This handles complex combined variations
    all_variations = set(generate_variation_list(word1, "all"))
    if word2_norm in all_variations:
        return (True, "combined_variation")
    
    return (False, None)


def apply_all_patterns_from_list(current_variations, pattern_key, bidirectional=True, positional=False):
    """
    Apply all patterns from a given pattern key to current variations.
    
    Args:
        current_variations: Set of current word variations
        pattern_key: Key in VARIATION_PATTERNS to apply
        bidirectional: If True, apply patterns in both directions
        positional: If True, use positional variation for ει↔ι pattern
    
    Returns:
        Set of new variations after applying patterns
    """
    new_variations = set()
    patterns = VARIATION_PATTERNS[pattern_key]
    
    for var in current_variations:
        new_variations.add(var)
        for pattern_group in patterns:
            if len(pattern_group) == 2:
                # Strip accents from patterns to match the stripped word
                p1, p2 = strip_accents(pattern_group[0]), strip_accents(pattern_group[1])
                # Special handling for ει↔ι with positional variations
                if positional and pattern_key == 'diphthong' and ((p1 == 'ει' and p2 == 'ι') or (p1 == 'ι' and p2 == 'ει')):
                    if 'ει' in var:
                        new_variations.update(generate_positional_variations(var, 'ει', 'ι'))
                    if 'ι' in var:
                        new_variations.update(generate_positional_variations(var, 'ι', 'ει'))
                else:
                    # Standard bidirectional replacement
                    if p1 in var:
                        new_variations.add(var.replace(p1, p2))
                    if bidirectional and p2 in var:
                        new_variations.add(var.replace(p2, p1))
            elif len(pattern_group) == 3:
                # Strip accents from patterns to match the stripped word
                p1, p2, p3 = strip_accents(pattern_group[0]), strip_accents(pattern_group[1]), strip_accents(pattern_group[2])
                # Apply all pairwise replacements
                if p1 in var:
                    new_variations.add(var.replace(p1, p2))
                    new_variations.add(var.replace(p1, p3))
                if p2 in var:
                    new_variations.add(var.replace(p2, p1))
                    new_variations.add(var.replace(p2, p3))
                if p3 in var:
                    new_variations.add(var.replace(p3, p1))
                    new_variations.add(var.replace(p3, p2))
    
    return new_variations


def generate_variation_list(base_word, variation_type="all"):
    """
    Generate possible variations of a base word.
    
    Args:
        base_word: The word to generate variations for
        variation_type: Type of variation ("lambda_future", "all", etc.)
    
    Returns:
        List of possible variant spellings (normalized, without accents)
    """
    word_norm = strip_accents(base_word.lower())
    current_variations = {word_norm}
    
    # Map variation types to pattern keys
    type_to_patterns = {
        'lambda_future': ['lambda_future'],
        'destruction': ['destruction'],
        'generation': ['generation'],
        'circumcision': ['circumcision'],
        'vowel': ['vowel_contraction', 'diphthong', 'ablaut'],
        'aorist': ['aorist_vowel', 'aorist_consonant', 'consonant_cluster'],
        'dialectal': ['dialectal'],
        'compound': ['compound_prefix'],
        'participle': ['participle'],
    }
    
    # Determine which patterns to apply
    if variation_type == "all":
        patterns_to_apply = list(VARIATION_PATTERNS.keys())
    elif variation_type in type_to_patterns:
        patterns_to_apply = type_to_patterns[variation_type]
    else:
        patterns_to_apply = []
    
    # Apply each pattern group
    for pattern_key in patterns_to_apply:
        if pattern_key not in VARIATION_PATTERNS:
            continue
        
        # Special handling for diphthong patterns (positional variations for ει↔ι)
        if pattern_key == 'diphthong':
            current_variations = apply_all_patterns_from_list(
                current_variations, pattern_key, bidirectional=True, positional=True
            )
        else:
            current_variations = apply_all_patterns_from_list(
                current_variations, pattern_key, bidirectional=True
            )
    
    # Add variations with movable nu
    final_variations = set(current_variations)
    for var in current_variations:
        if var.endswith('ε') or var.endswith('ι'):
            final_variations.add(var + 'ν')
        elif var.endswith('εν') or var.endswith('ιν'):
            final_variations.add(var[:-1])
    
    return list(final_variations)


if __name__ == '__main__':
    # Example usage
    print("Valid Variation Patterns for Brenton LXX")
    print("="*60)
    
    # Test lambda future detection
    test_pairs = [
        ("λήψομαι", "λήμψομαι"),
        ("ἀναλήψεται", "ἀναλήμψεται"),
        ("συλλήψῃ", "συλλήμψῃ"),
        ("ἐξολοθρεύσω", "ἐξολεθρεύσω"),
        ("γεννήματος", "γενήματος"),
    ]
    
    print("\nTesting variation detection:")
    for word1, word2 in test_pairs:
        is_var, var_type = is_likely_legitimate_variation(word1, word2)
        if is_var:
            print(f"✓ {word1} ↔ {word2}: {var_type}")
        else:
            print(f"✗ {word1} ↔ {word2}: not recognized")
    
    # Generate variations for a sample word
    print("\n\nGenerating variations for 'καταλήψομαι':")
    variations = generate_variation_list("καταλήψομαι", "lambda_future")
    for var in variations:
        print(f"  - {var}")
