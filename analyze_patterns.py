#!/usr/bin/env python3
"""
Analyze patterns in word corrections and accepted words.
"""

import csv
import re
from collections import defaultdict, Counter

def normalize_for_comparison(word):
    """Remove diacritics for easier pattern comparison."""
    import unicodedata
    nfd = unicodedata.normalize('NFD', word)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')

def analyze_corrections():
    """Analyze transcription error patterns in word_corrections.tsv"""
    corrections = []
    with open('word_corrections.tsv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if len(row) >= 3:
                verse = row[0]
                wrong = row[1]
                right = row[2]
                corrections.append((verse, wrong, right))
    
    print("TRANSCRIPTION ERROR PATTERNS")
    print("="*70)
    print(f"Total corrections: {len(corrections)}\n")
    
    # Analyze character substitutions
    substitutions = Counter()
    insertions = []
    deletions = []
    transpositions = []
    
    for verse, wrong, right in corrections:
        wrong_norm = normalize_for_comparison(wrong)
        right_norm = normalize_for_comparison(right)
        
        if len(wrong) == len(right):
            # Same length - check for substitutions or transpositions
            diffs = [(i, wrong[i], right[i]) for i in range(len(wrong)) if wrong[i] != right[i]]
            
            if len(diffs) == 1:
                pos, w_char, r_char = diffs[0]
                substitutions[(w_char, r_char)] += 1
            elif len(diffs) == 2:
                # Possible transposition
                i1, w1, r1 = diffs[0]
                i2, w2, r2 = diffs[1]
                if i2 == i1 + 1 and w1 == r2 and w2 == r1:
                    transpositions.append((wrong, right, w1+w2, r1+r2))
        
        elif len(wrong) < len(right):
            # Missing character(s)
            insertions.append((wrong, right))
        
        elif len(wrong) > len(right):
            # Extra character(s)
            deletions.append((wrong, right))
    
    print("\n1. CHARACTER SUBSTITUTIONS (OCR/transcription errors):")
    print("-"*70)
    for (wrong_c, right_c), count in substitutions.most_common(30):
        print(f"  {wrong_c} → {right_c}: {count} occurrences")
    
    print("\n\n2. COMMON INSERTION ERRORS (missing characters):")
    print("-"*70)
    for wrong, right in insertions[:15]:
        print(f"  {wrong} → {right}")
    
    print("\n\n3. COMMON DELETION ERRORS (extra characters):")
    print("-"*70)
    for wrong, right in deletions[:15]:
        print(f"  {wrong} → {right}")
    
    if transpositions:
        print("\n\n4. TRANSPOSITION ERRORS:")
        print("-"*70)
        for wrong, right, w_chars, r_chars in transpositions[:10]:
            print(f"  {wrong} → {right} (swapped {w_chars} ↔ {r_chars})")


def analyze_accepted_words():
    """Analyze legitimate spelling variations in accepted_words.txt"""
    
    # Load accepted words
    accepted = []
    with open('accepted_words.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                accepted.append(line)
    
    print("\n\n")
    print("="*70)
    print("LEGITIMATE BRENTON SPELLING VARIATIONS")
    print("="*70)
    print(f"Total accepted words: {len(accepted)}\n")
    
    # Categorize by pattern
    categories = defaultdict(list)
    
    for word in accepted:
        word_lower = word.lower()
        
        # Lambda future forms (λήψ- vs λημψ-)
        if 'λήψ' in word_lower or 'λημψ' in word_lower:
            categories['Lambda future (λήψ- vs λημψ-)'].append(word)
        
        # Aorist passive forms (-ληφθ- vs -λημφθ-)  
        elif 'ληφθ' in word_lower or 'λημφθ' in word_lower or 'ληψθ' in word_lower:
            categories['Aorist passive (λήφθη vs λήμφθη)'].append(word)
        
        # Destruction verbs (ὀλοθρ- vs ὀλεθρ- and ἐξολοθρ- vs ἐξολεθρ-)
        elif 'ολοθρ' in word_lower or 'ολεθρ' in word_lower:
            categories['Destruction verbs (ὀλοθρ- vs ὀλεθρ-)'].append(word)
        
        # Loan/borrow verbs (δανε- vs δανι-)
        elif 'δανε' in word_lower or 'δανι' in word_lower:
            categories['Loan verbs (δανε- vs δανι-)'].append(word)
        
        # Circumcision forms (περιτεμ- variations)
        elif 'περιτεμ' in word_lower:
            categories['Circumcision (περιτεμ- variations)'].append(word)
        
        # Generation/produce words (γενν- vs γενη-)
        elif 'γενν' in word_lower or 'γενημ' in word_lower or 'γεννημ' in word_lower:
            categories['Generation/produce (γενν- vs γενη-)'].append(word)
        
        # Command verbs (ἐντ- variations)
        elif 'ἀντέλλ' in word_lower or 'ἐντέλλ' in word_lower or 'ἐντλλ' in word_lower:
            categories['Command verbs (ἐντέλλ- variations)'].append(word)
        
        # Other compound verb variations
        elif any(prefix in word_lower for prefix in ['κατα', 'ἐπι', 'ἀπο', 'συν', 'ἐξ', 'ἀν']):
            if len(word) > 8:  # Long compounds
                categories['Compound verb variations'].append(word)
        
        # Contractions and vowel changes
        elif 'ώ' in word or 'εί' in word or 'οι' in word:
            categories['Vowel variations/contractions'].append(word)
        
        else:
            categories['Other variations'].append(word)
    
    for category, words in sorted(categories.items()):
        print(f"\n{category}:")
        print("-"*70)
        for word in sorted(words)[:20]:  # Show first 20
            print(f"  {word}")
        if len(words) > 20:
            print(f"  ... and {len(words) - 20} more")


if __name__ == '__main__':
    analyze_corrections()
    analyze_accepted_words()
