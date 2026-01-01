# Find Errors - Brenton LXX Error Detection

A Python tool to identify potential errors and discrepancies in Brenton's Septuagint (LXX) text by comparing it against the Rahlfs and Swete editions.

## Purpose

This folder contains scripts to analyze the Greek text of Brenton's English Septuagint edition (`Brenton.tex`) and identify words that don't appear in two authoritative Septuagint editions:
- **Rahlfs Edition** (rahlfs_words.csv, rahlfs_versification.csv)
- **Swete Edition** (swete_words.csv, swete_versification.csv)

The tool helps identify:
- **Typographical errors** (typos with high similarity to known words)
- **OCR errors** (from scanning physical texts)
- **Proper names** (not always in word lists)
- **Number words** (may vary between editions)
- **Accepted variations** (maintained in accepted_words.txt)

The script performs verse-specific checking, looking first in the exact verse, then in surrounding verses (±20 verses), and finally in the broader corpus to identify likely typos with high confidence.

## Folder Structure

```
check_missing_words_for_typos/
├── README.md                         # This file
├── PATTERN_ANALYSIS.md               # Analysis of error patterns
├── VARIATION_INTEGRATION.md          # Spelling variation documentation
├── check_missing_words_for_typos.py  # Main analysis script
├── compare-brenton-swete.py          # Additional comparison script
├── analyze_patterns.py               # Analyze error patterns in corrections
├── valid_variation_patterns.py       # Legitimate spelling variation generator
├── book_code_mappings.py             # Greek book name to edition code mappings
├── test_lettrine.py                  # Unit tests for LaTeX lettrine parsing
├── test_verse_lookup.py              # Unit tests for verse reference conversion
├── output/
│   ├── missing_words.tsv             # Output: all missing words
│   ├── missing_words_typo_check.tsv  # Output: full analysis with flags
│   ├── missing_words_likely_typos.tsv # Output: filtered likely typos
│   ├── missing_words_legitimate_variations.tsv # Output: valid spelling variations
│   └── missing_words_unmatched.tsv   # Output: words needing manual review
└── logs/                             # Execution logs
```

## Requirements

- Python 3.x
- No external dependencies (uses standard library only)

## Quick Start

```bash
cd check_missing_words_for_typos
python3 check_missing_words_for_typos.py
```

Or with logging:

```bash
cd check_missing_words_for_typos
python3 -u check_missing_words_for_typos.py |& tee "logs/script_run-$(date +%s).log"
```

## Command-Line Options

```bash
# Run without typo checking (faster):
python3 check_missing_words_for_typos.py --no-typo-check

# Specify custom input files:
python3 check_missing_words_for_typos.py --bible ../input/MyBible.tex --rahlfs ../input/my_rahlfs.csv

# See all options:
python3 check_missing_words_for_typos.py --help
```

Available options:
- `--bible` - Path to Bible .tex file (default: ../input/Brenton.tex)
- `--rahlfs` - Path to Rahlfs words CSV (default: ../input/rahlfs_words.csv)
- `--swete` - Path to Swete words CSV (default: ../input/swete_words.csv)
- `--rahlfs-versification` - Path to Rahlfs versification CSV (default: ../input/rahlfs_versification.csv)
- `--swete-versification` - Path to Swete versification CSV (default: ../input/swete_versification.csv)
- `--output` - Path to output TSV file (default: output/missing_words.tsv)
- `--accepted-words` - Path to accepted words file (default: ../accepted_words.txt)
- `--already-examined` - Path to already examined corrections (default: ../word_corrections.tsv)
- `--no-typo-check` - Disable typo checking for faster processing

## Output Files

The script generates multiple output files in the `output/` directory:

### 1. `missing_words.tsv`
Basic list of all words not found in either Rahlfs or Swete:
- Line Number
- Verse Reference (e.g., ΓΕΝΕΣΙΣ 14:7)
- Word
- Full Line (LaTeX source)

### 2. `missing_words_typo_check.tsv`
Complete analysis with additional columns:
- Is Name? (Likely proper name)
- Is Number? (Likely number word)
- Likely Typo? (High similarity to known word)
- Closest Match (Most similar word found)
- Similarity (0.00-1.00 ratio)
- Verse Match? (Found in same verse)
- Area Match? (Found within ±20 verses)
- Legitimate Variation? (Valid spelling difference)

### 3. `missing_words_likely_typos.tsv`
Filtered list containing only probable typos (excluding proper names, numbers, and legitimate variations):
- Focus on words with ≥80% similarity to known words
- Prioritizes verse-specific matches
- Ideal starting point for manual review

### 4. `missing_words_legitimate_variations.tsv`
Words identified as valid spelling variations between editions.

### 5. `missing_words_unmatched.tsv`
Words that need manual review (not identified as variations or numbers).

## How It Works

1. **Load Reference Data**
   - Loads word lists from Rahlfs and Swete CSV files
   - Normalizes all text using Unicode NFC normalization
   - Strips diacritical marks for comparison

2. **Process Brenton.tex**
   - Extracts Greek words using regex (excludes LaTeX commands)
   - Tracks current book, chapter, and verse using LaTeX markup
   - Identifies words not present in either reference edition

3. **Typo Detection** (optional, enabled by default)
   - First checks exact verse for similar words
   - Then checks surrounding area (±20 verses)
   - Falls back to broader corpus search
   - Uses sequence matching to find words with ≥80% similarity
   - Flags proper names (capitalized words)
   - Flags number words (contains Greek number patterns)

4. **Output Generation**
   - Writes results to TSV files in `output/`
   - Logs execution details for review

## Book Code Mappings

The `book_code_mappings.py` module handles conversions between:
- **Brenton**: Greek book names (e.g., ΓΕΝΕΣΙΣ, ΕΞΟΔΟΣ)
- **Swete**: Short codes (e.g., Gen, Exo, 1Sa, 1Ki)
- **Rahlfs**: Standard codes (e.g., Gen, Exod, 1Sam, 1Kgs)

Special handling:
- Ezra-Nehemiah are combined in Rahlfs (2Esdr) but separate in Brenton
- Nehemiah chapters are offset by +10 in Rahlfs (e.g., Neh 1 = 2Esdr 11)
- Multiple versions exist for some books (Joshua A/B, Daniel OG/Theodotion)

## Accepted Words

The `input/accepted_words.txt` file contains words that have been manually verified as correct variations or acceptable differences. Words in this file are skipped during processing. Format:
- One word per line
- Lines starting with `#` are comments
- Words should match the normalized form (lowercase, diacritics stripped)

## Word Corrections

The `../word_corrections.tsv` file (at project root) tracks previously identified errors and their corrections. This file:
- Allows the script to skip words already examined
- Is shared with the `apply_corrections/` workflow for applying fixes

Format:
- Tab-separated values (TSV)
- Three columns: Verse Reference, Incorrect Word, Corrected Word
- Example: `ΓΕΝΕΣΙΣ 5:10	ἑπτκόσια	ἑπτακόσια`
- Special entries can use `ALL` for verse reference to apply across all verses

## Workflow Integration

This folder is part of the larger error-finding and correction workflow:

1. **Find errors** (this folder) - Identify potential errors in Brenton.tex
2. **Review & document** - Add corrections to `../word_corrections.tsv`
3. **Apply corrections** (`../apply_corrections/`) - Apply fixes to LaTeX source files

## Additional Scripts

- **analyze_patterns.py** - Analyzes transcription error patterns in the corrections file
- **compare-brenton-swete.py** - Detailed comparison between Brenton and Swete editions
- **valid_variation_patterns.py** - Generates legitimate Greek spelling variations

## License

This project is for academic and research purposes, analyzing public domain Septuagint texts.
