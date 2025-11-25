#!/usr/bin/env python3
"""
Valid Greek spelling variation patterns for Brenton LXX.
These are legitimate textual/dialectal variants that should NOT be flagged as errors.
"""

import unicodedata

def strip_accents(text):
    """Remove Greek accents for pattern matching."""
    # Normalize to NFD (decomposed form) so accents are separate
    nfd = unicodedata.normalize('NFD', text)
    # Filter out combining marks (accents)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')

# ============================================================================
# MORPHOLOGICAL VARIATIONS (Verb Forms)
# ============================================================================

# Lambda Future Stems (λήψ- vs λήμψ-)
# Both forms are valid in Greek for the future of λαμβάνω and compounds
LAMBDA_FUTURE_PATTERNS = [
    ('λήψ', 'λημψ'),      # Simple forms: λήψομαι ↔ λήμψομαι
    ('λήψ', 'λήμψ'),      # Alternative with breathing
    ('ληψ', 'λημψ'),      # Without diacritics for comparison
]

# Compounds of λαμβάνω with lambda future variation
LAMBDA_COMPOUNDS = [
    'ἀναλήψ',    'ἀναλημψ',      # take up
    'ἀντιλήψ',   'ἀντιλημψ',     # take hold of, help
    'ἐπιλήψ',    'ἐπιλημψ',      # seize, take hold
    'καταλήψ',   'καταλημψ',     # seize, overtake
    'μεταλήψ',   'μεταλημψ',     # partake
    'παραλήψ',   'παραλημψ',     # receive, take
    'περιλήψ',   'περιλημψ',     # embrace, comprehend
    'προκαταλήψ', 'προκαταλημψ', # seize beforehand
    'προλήψ',    'προλημψ',      # anticipate
    'συλλήψ',    'συλλημψ',      # conceive, seize
    'συμπαραλήψ', 'συμπαραλημψ', # take along with
    'συμπεριλήψ', 'συμπεριλημψ', # include with
    'συναντιλήψ', 'συναντιλημψ', # help together
    'ὑπολήψ',    'ὑπολημψ',      # suppose, take up
]

# Aorist Passive (λήφθη vs λήμφθη vs ληφθη)
AORIST_PASSIVE_LAMBDA = [
    ('ληφθ', 'λημφθ'),    # ἐλήφθη ↔ ἐλήμφθη
    ('λήφθ', 'λήμφθ'),    
    ('ληψθ', 'λημψθ'),    # Alternative forms
]

# ============================================================================
# DESTRUCTION VERBS (ὀλοθρ- vs ὀλεθρ-)
# ============================================================================

# Both roots exist in Greek manuscripts
DESTRUCTION_VERB_VARIATIONS = [
    ('ολοθρ', 'ολεθρ'),         # General stem (no accents)
    ('ολοθρευ', 'ολεθρευ'),     # ὀλοθρεύω ↔ ὀλεθρεύω
    ('ξολοθρ', 'ξολεθρ'),       # ἐξολοθρεύω ↔ ἐξολεθρεύω (no accents)
    ('ξωλοθρ', 'ξωλεθρ'),       # Intensive form (no accents)
]

# ============================================================================
# LOAN/BORROW VERBS (δανε- vs δανι-)
# ============================================================================

LOAN_VERB_VARIATIONS = [
    ('δανε', 'δανι'),           # δανείζω ↔ δανίζω
    ('δανειζ', 'δανιζ'),
    ('δανεισ', 'δανισ'),
]

# ============================================================================
# GENERATION/PRODUCE WORDS (γενν- vs γενη-)
# ============================================================================

# Double nu vs single nu with eta
GENERATION_VARIATIONS = [
    ('γεννημ', 'γενημ'),        # γέννημα ↔ γένημα (produce, fruit)
    ('γεννηματ', 'γενηματ'),    # γεννήματος ↔ γενήματος
    ('εννημ', 'ενημ'),          # Pattern without initial gamma
]

# ============================================================================
# COMMAND VERBS (ἐντέλλ- variations)
# ============================================================================

COMMAND_VERB_VARIATIONS = [
    ('ἐντελλ', 'ἀντελλ'),       # ἐντέλλομαι ↔ ἀντέλλομαι (less common)
    ('ἐντελ', 'ἐντλ'),          # Occasional contraction
]

# ============================================================================
# CIRCUMCISION VERBS
# ============================================================================

CIRCUMCISION_VARIATIONS = [
    ('περιτεμεσθ', 'περιτεμνεσθ'),  # infinitive variations
    ('περιτεμε', 'περιτεμνε'),
]

# ============================================================================
# VOWEL CONTRACTIONS AND VARIATIONS
# ============================================================================

# Omega vs omicron-epsilon in various contexts
VOWEL_CONTRACTIONS = [
    ('εω', 'ω'),                # Standard contraction
    ('οε', 'ου'),               # Contraction
    ('αε', 'α'),                # Contraction
    ('αο', 'ω'),                # Contraction
    ('εε', 'ει'),               # Contraction
]

# Diphthong variations
DIPHTHONG_VARIATIONS = [
    ('ει', 'ι'),                # ει ↔ ι (iotacism in later Greek)
    ('οι', 'υ'),                # οι ↔ υ (rare)
    ('αι', 'ε'),                # αι ↔ ε (in some dialects)
]

# Long vs short vowel (ablaut)
ABLAUT_VARIATIONS = [
    ('ε', 'η'),                 # Short vs long e
    ('ο', 'ω'),                 # Short vs long o
    ('α', 'η'),                 # In some contexts
]

# ============================================================================
# VERB STEM VARIATIONS
# ============================================================================

# Aorist forms with vowel variation
AORIST_VOWEL_VARIATIONS = [
    ('φειλ', 'φηλ'),            # ἀφείλετο ↔ ἀφήλετο (rare)
    ('ειλ', 'ηλ'),              # In aorist middle forms
]

# Sigma vs theta in aorists
AORIST_CONSONANT_VARIATIONS = [
    ('θη', 'ση'),               # Passive aorist variations
]

# ============================================================================
# COMPOUND VERB PREFIX VARIATIONS
# ============================================================================

# Vowel elision/crasis in compounds
COMPOUND_PREFIX_VARIATIONS = [
    ('προσ', 'προ'),            # Before consonants
    ('κατα', 'κατ', 'καθ'),     # Before vowels/aspirates
    ('ἀπο', 'ἀπ', 'ἀφ'),        # Before vowels/aspirates
    ('ἐπι', 'ἐπ', 'ἐφ'),        # Before vowels/aspirates
    ('συν', 'συ', 'συμ'),       # Assimilation before different consonants
]

# ============================================================================
# PARTICIPLE VARIATIONS
# ============================================================================

# Different participial endings
PARTICIPLE_VARIATIONS = [
    ('ουσ', 'οντ'),             # Present active participle
    ('ων', 'οντ'),              # Masculine forms
    ('ομεν', 'ωμεν'),           # Subjunctive vs indicative
]

# ============================================================================
# SPECIFIC WORD VARIATIONS
# ============================================================================

# Words with attested variant spellings
SPECIFIC_WORD_VARIANTS = {
    # Monetary terms
    'δίδραγμον': ['διδραχμον', 'δίδραχμον'],
    
    # Jewelry
    'ψέλλιον': ['ψέλιον', 'ψελλιον'],
    
    # Chimera/torrent variations (χιμ- vs χειμ-)
    'χιμάρρο': ['χειμάρρο', 'χειμάῤῥο', 'χιμάῤῥο'],
    
    # Early rain (πρώϊμον vs πρόϊμον)
    'πρώϊμον': ['πρόϊμον', 'πρόιμον', 'πρωϊμον'],
    
    # Pelican variations
    'πελακάν': ['πελεκάν'],
    
    # Abomination
    'βδέλυμα': ['βδέλυγμα'],
    
    # Bearer/nurse (τροφο- variations)
    'τροφοφορ': ['τροπο φορ'],  # Compound variation
    
    # Enmity/opposition
    'ἐξεναντί': ['ἐναντί'],
}

# ============================================================================
# SYSTEMATIC LETTER CONFUSIONS (Not errors, but dialectal)
# ============================================================================

# These are attested variations in different manuscript traditions
DIALECTAL_LETTER_VARIATIONS = [
    ('ρρ', 'ρ'),                # Single vs double rho
    ('λλ', 'λ'),                # Single vs double lambda
    ('σσ', 'σ'),                # Single vs double sigma
    ('ττ', 'τ'),                # Single vs double tau
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def has_lambda_future_variation(word1, word2):
    """Check if two words differ only in lambda future stem."""
    word1_norm = strip_accents(word1.lower())
    word2_norm = strip_accents(word2.lower())
    
    for pattern1, pattern2 in LAMBDA_FUTURE_PATTERNS:
        if pattern1 in word1_norm and pattern2 in word2_norm:
            # Check if substituting one pattern for other makes them match
            if word1_norm.replace(pattern1, pattern2) == word2_norm:
                return True
            if word2_norm.replace(pattern2, pattern1) == word1_norm:
                return True
    
    # Check compound variations
    for i in range(0, len(LAMBDA_COMPOUNDS), 2):
        comp1 = LAMBDA_COMPOUNDS[i]
        comp2 = LAMBDA_COMPOUNDS[i + 1]
        if comp1 in word1_norm and comp2 in word2_norm:
            if word1_norm.replace(comp1, comp2) == word2_norm:
                return True
            if word2_norm.replace(comp2, comp1) == word1_norm:
                return True
    
    return False


def has_destruction_verb_variation(word1, word2):
    """Check if two words differ only in destruction verb stem."""
    word1_norm = strip_accents(word1.lower())
    word2_norm = strip_accents(word2.lower())
    
    for pattern1, pattern2 in DESTRUCTION_VERB_VARIATIONS:
        if (pattern1 in word1_norm or pattern2 in word1_norm) and \
           (pattern1 in word2_norm or pattern2 in word2_norm):
            if word1_norm.replace(pattern1, pattern2) == word2_norm:
                return True
            if word2_norm.replace(pattern2, pattern1) == word1_norm:
                return True
    
    return False


def has_generation_variation(word1, word2):
    """Check if two words differ only in generation/produce word stem."""
    word1_norm = strip_accents(word1.lower())
    word2_norm = strip_accents(word2.lower())
    
    for pattern1, pattern2 in GENERATION_VARIATIONS:
        if (pattern1 in word1_norm or pattern2 in word1_norm) and \
           (pattern1 in word2_norm or pattern2 in word2_norm):
            if word1_norm.replace(pattern1, pattern2) == word2_norm:
                return True
            if word2_norm.replace(pattern2, pattern1) == word1_norm:
                return True
    
    return False


def is_likely_legitimate_variation(word1, word2):
    """
    Check if two words represent a likely legitimate spelling variation
    rather than a transcription error.
    
    Returns (is_variation, variation_type) tuple.
    """
    if has_lambda_future_variation(word1, word2):
        return (True, "lambda_future")
    
    if has_destruction_verb_variation(word1, word2):
        return (True, "destruction_verb")
    
    if has_generation_variation(word1, word2):
        return (True, "generation_word")
    
    # Check loan verb variations
    word1_norm = strip_accents(word1.lower())
    word2_norm = strip_accents(word2.lower())
    for pattern1, pattern2 in LOAN_VERB_VARIATIONS:
        if pattern1 in word1_norm and pattern2 in word2_norm:
            if word1_norm.replace(pattern1, pattern2) == word2_norm:
                return (True, "loan_verb")
    
    # Check command verb variations
    for pattern1, pattern2 in COMMAND_VERB_VARIATIONS:
        if pattern1 in word1_norm and pattern2 in word2_norm:
            if word1_norm.replace(pattern1, pattern2) == word2_norm:
                return (True, "command_verb")
    
    # Check circumcision variations
    for pattern1, pattern2 in CIRCUMCISION_VARIATIONS:
        if pattern1 in word1_norm and pattern2 in word2_norm:
            if word1_norm.replace(pattern1, pattern2) == word2_norm:
                return (True, "circumcision_verb")
    
    return (False, None)


def generate_variation_list(base_word, variation_type="all"):
    """
    Generate possible variations of a base word.
    
    Args:
        base_word: The word to generate variations for
        variation_type: Type of variation ("lambda_future", "all", etc.)
    
    Returns:
        List of possible variant spellings
    """
    variations = set([base_word])
    word_norm = strip_accents(base_word.lower())
    
    if variation_type in ["lambda_future", "all"]:
        # Lambda future variations
        for pattern1, pattern2 in LAMBDA_FUTURE_PATTERNS:
            if pattern1 in word_norm:
                variations.add(word_norm.replace(pattern1, pattern2))
            if pattern2 in word_norm:
                variations.add(word_norm.replace(pattern2, pattern1))
        
        # Lambda compound variations
        for i in range(0, len(LAMBDA_COMPOUNDS), 2):
            comp1 = LAMBDA_COMPOUNDS[i]
            comp2 = LAMBDA_COMPOUNDS[i + 1]
            if comp1 in word_norm:
                variations.add(word_norm.replace(comp1, comp2))
            if comp2 in word_norm:
                variations.add(word_norm.replace(comp2, comp1))
    
    if variation_type in ["destruction", "all"]:
        # Destruction verb variations
        for pattern1, pattern2 in DESTRUCTION_VERB_VARIATIONS:
            if pattern1 in word_norm:
                variations.add(word_norm.replace(pattern1, pattern2))
            if pattern2 in word_norm:
                variations.add(word_norm.replace(pattern2, pattern1))
    
    if variation_type in ["generation", "all"]:
        # Generation word variations
        for pattern1, pattern2 in GENERATION_VARIATIONS:
            if pattern1 in word_norm:
                variations.add(word_norm.replace(pattern1, pattern2))
            if pattern2 in word_norm:
                variations.add(word_norm.replace(pattern2, pattern1))
    
    return list(variations)


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
