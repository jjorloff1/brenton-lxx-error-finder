#!/usr/bin/env python3
import re

def extract_greek_words_test(line):
    """Test version of extract_greek_words."""
    words = []
    
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
        
        words.append(first_word)
        
        # Remove the \lettrine command from the line for further processing
        line = line[:lettrine_match.start()] + line[lettrine_match.end():]
    
    # Match remaining Greek words
    greek_pattern = r'[\u0370-\u03FF\u1F00-\u1FFF]+'
    remaining_words = re.findall(greek_pattern, line)
    words.extend([w for w in remaining_words])
    
    return words

def test_lettrine():
    """Test the lettrine pattern matching."""
    
    # Test cases from the actual file
    test_cases = [
        (r'\lettrine[lines=2, loversize=0.2, nindent=0em, findent=.25em]{\textcolor{bookheadingcolor}{Ἐ}}{Ν} ἀρχῇ ἐποίησεν', 
         'ἐν'),
        (r'\lettrine[lines=2, loversize=0.2, nindent=0em, findent=.25em]{\textcolor{bookheadingcolor}{Φ}}{ΙΛΟΣΟΦΩΤΑΤΟΝ} λόγον', 
         'φιλοσοφωτατον'),
        (r'\lettrine[lines=2, loversize=0.2, nindent=0em, findent=.25em]{Κ}{ΑΙ} ἐγένετο', 
         'και'),
    ]
    
    print("Testing extract_greek_words function with lettrine handling:\n")
    all_passed = True
    
    for i, (test_line, expected_first) in enumerate(test_cases, 1):
        print(f"Test case {i}:")
        print(f"  Line: {test_line[:80]}...")
        
        words = extract_greek_words_test(test_line)
        
        if words:
            print(f"  ✓ Extracted words: {words}")
            if words[0] == expected_first:
                print(f"  ✓ First word matches expected: '{expected_first}'")
            else:
                print(f"  ✗ FAIL: Expected '{expected_first}', got '{words[0]}'")
                all_passed = False
        else:
            print(f"  ✗ NO WORDS EXTRACTED")
            all_passed = False
        print()
    
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")

if __name__ == '__main__':
    test_lettrine()


