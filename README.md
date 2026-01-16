# Brenton LXX Error Finder

A project to identify and correct errors in Brenton's Septuagint (LXX) Greek text by comparing it against the Rahlfs and Swete editions.

## Overview

This project provides a complete workflow for:
1. **Finding errors** in Brenton's Septuagint text
2. **Documenting corrections** in a central corrections file
3. **Applying corrections** to LaTeX source files

The workflow compares Brenton's Greek text against two authoritative Septuagint editions (Rahlfs and Swete) to identify typographical errors, OCR mistakes, and other discrepancies.

## Project Structure

```
brenton-lxx-error-finder/
├── README.md                       # This file
├── word_corrections.tsv            # Central corrections file (shared between workflows)
├── accepted_words.txt              # Manually verified acceptable word variations
├── accepted_sequence_variants.tsv  # Verse-specific accepted textual variants
├── input/                          # Shared input files
│   ├── Brenton.tex                 # Source text (LaTeX format)
│   ├── enclitics_proclitics.txt    # Valid unaccented word forms (for check_unaccented_words)
│   ├── rahlfs_words.csv            # Word list from Rahlfs edition
│   ├── rahlfs_versification.csv    # Verse reference mappings (Rahlfs)
│   ├── swete_words.csv             # Word list from Swete edition
│   └── swete_versification.csv     # Verse reference mappings (Swete)
├── shared/                         # Shared utility modules
│   ├── greek_utils.py              # Text normalization and Greek processing
│   ├── data_loaders.py             # CSV and versification loading
│   └── book_code_mappings.py       # Verse reference conversion between editions
├── check_missing_words_for_typos/  # Vocabulary-based error detection
│   ├── README.md                   # Detailed documentation
│   ├── check_missing_words_for_typos.py  # Main script
│   ├── output/                     # Analysis results (missing_words*.tsv)
│   └── logs/                       # Execution logs
├── check_sequence_errors/          # Sequence-based error detection
│   ├── README.md                   # Detailed documentation
│   ├── check_sequence_errors.py    # Main script
│   └── output/                     # Analysis results (sequence_errors.tsv)
├── check_grave_accents/            # Misplaced grave accent detection
│   ├── README.md                   # Detailed documentation
│   ├── check_grave_accents.py      # Main script
│   └── output/                     # Analysis results (misplaced_graves.tsv)
├── check_multiple_accents/         # Multiple accent detection (merged words)
│   ├── README.md                   # Detailed documentation
│   ├── check_multiple_accents.py   # Main script
│   └── output/                     # Analysis results (multiple_accents.tsv)
├── check_unaccented_words/         # Missing accent detection (using enclitic/proclitic list)
│   ├── README.md                   # Detailed documentation
│   ├── check_unaccented_words.py   # Main script
│   └── output/                     # Analysis results (unaccented_sequences.tsv, consecutive_enclitics.tsv)
├── apply_corrections/              # Correction application scripts
│   ├── README.md                   # Detailed documentation
│   ├── apply_corrections.py        # Script to apply corrections to LaTeX
│   ├── grcbrent_xetex_original/    # Original LaTeX source files
│   └── grcbrent_xetex_corrected/   # Corrected LaTeX output files
└── contributor_analysis/           # Files for manual verification by contributors
```

## Quick Start

### Find Vocabulary Errors
```bash
cd check_missing_words_for_typos
python3 -u check_missing_words_for_typos.py |& tee "logs/script_run-$(date +%s).log"
```
Results are written to `check_missing_words_for_typos/output/`.

### Find Sequence Errors
```bash
cd check_sequence_errors
python3 check_sequence_errors.py
```
Results are written to `check_sequence_errors/output/`.

### Find Misplaced Grave Accents
```bash
cd check_grave_accents
python3 check_grave_accents.py
```
Results are written to `check_grave_accents/output/`.

### Find Multiple Accents (Merged Words)
```bash
cd check_multiple_accents
python3 check_multiple_accents.py
```
Results are written to `check_multiple_accents/output/`.

### Find Missing Accents
```bash
cd check_unaccented_words
python3 check_unaccented_words.py
```
Results are written to `check_unaccented_words/output/`.

### Apply Corrections
```bash
cd apply_corrections
python3 apply_corrections.py
```
Corrected files are written to `apply_corrections/grcbrent_xetex_corrected/`.

## Workflow

### 1. Find Errors

Two complementary approaches detect different error types:

#### Vocabulary-Based Detection (`check_missing_words_for_typos/`)

The `check_missing_words_for_typos.py` script:
- Reads the Brenton Greek text (`input/Brenton.tex`)
- Compares each word against Rahlfs and Swete word lists
- Identifies words not found in either reference edition
- Performs typo detection using similarity matching
- Generates output files categorizing potential errors

Key outputs:
- `missing_words_likely_typos.tsv` - High-confidence typos for review
- `missing_words_legitimate_variations.tsv` - Valid spelling differences
- `missing_words_unmatched.tsv` - Words needing manual review

**Catches:** Substitution, omission, fusion, fission, orthographic variation, visual confusion errors that result in non-words.

#### Sequence-Based Detection (`check_sequence_errors/`)

The `check_sequence_errors.py` script:
- Performs word-by-word alignment between Brenton and Rahlfs using `difflib.SequenceMatcher`
- Detects character substitutions that produce valid but incorrect Greek words
- Focuses on OCR-confusable characters: υ/ν/ς/σ, ε/η, ο/ω
- Detects multi-character sequence confusions: ην↔ης, οι↔αι

Key output:
- `sequence_errors.tsv` - Detected substitutions with verse, words, error type, context

**Catches:** Valid-word substitutions that vocabulary checking misses (e.g., `-ου` vs `-ον` endings are both valid Greek, but only one is correct in context).

### 2. Document Corrections (`word_corrections.tsv`)

After reviewing the error detection output, add corrections to `word_corrections.tsv`:
- Tab-separated format: `Verse Reference<tab>Incorrect Word<tab>Correct Word`
- Example: `ΓΕΝΕΣΙΣ 5:10	ἑπτκόσια	ἑπτακόσια`
- Use `ALL` for verse reference to apply correction globally

This file is shared between both workflows - errors found by `check_missing_words_for_typos/` are corrected via entries here, and `apply_corrections/` reads this file to apply the fixes.

### 3. Apply Corrections (`apply_corrections/`)

The `apply_corrections.py` script:
- Reads corrections from `../word_corrections.tsv`
- Applies them to LaTeX source files in `grcbrent_xetex_original/`
- Writes corrected files to `grcbrent_xetex_corrected/`
- Generates a detailed log of all changes

The script handles:
- Verse-specific corrections
- Global (`ALL`) corrections
- Diacritical mark fixes (breathing marks, etc.)
- Word boundary detection to avoid false matches

## Shared Files

### `word_corrections.tsv`
The central corrections file containing all identified errors and their corrections. This file:
- Is read by `check_missing_words_for_typos/` to skip already-corrected words
- Is read by `check_sequence_errors/` to skip already-corrected words
- Is read by `apply_corrections/` to apply fixes to source files

### `accepted_words.txt`
Words that are acceptable variations and should not be flagged as errors. Used by both detection scripts.

### `accepted_sequence_variants.tsv`
Verse-specific textual variants that are intentional differences between Brenton and Rahlfs (not OCR errors). Format:
```
Verse Reference<tab>Brenton Word<tab>Rahlfs Word
```
Example:
```
ΓΕΝΕΣΙΣ 3:8	τὴς	τὴν
```

### Reference Data
Located in `input/`:
- `Brenton.tex` - Source text (LaTeX format)
- `rahlfs_words.csv` / `swete_words.csv` - Word lists from reference editions
- `rahlfs_versification.csv` / `swete_versification.csv` - Verse mappings

## Additional Folders

### `contributor_analysis/`
Contains files for the manual verification process used by project contributors to help validate corrections. Not used by any scripts.

### `shared/`
Common utility modules used by both detection scripts:
- `brenton_parser.py` - Shared parser for Brenton.tex that yields verse context (book, chapter, verse, words) for each line
- `greek_utils.py` - Text normalization, diacritical handling, Greek word extraction, accent comparison
- `data_loaders.py` - CSV loading, versification data handling
- `book_code_mappings.py` - Verse reference conversion between Brenton and Rahlfs formats

## OCR Error Detection Approaches

This project uses multiple approaches to detect different categories of OCR errors:

### Currently Implemented

| Approach | Script | Error Types Detected |
|----------|--------|---------------------|
| **Vocabulary-Based** | `check_missing_words_for_typos.py` | Non-word errors: substitution, omission, fusion, fission, orthographic variation |
| **Sequence-Based** | `check_sequence_errors.py` | Valid-word substitutions: υ/ν/ς/σ, ε/η, ο/ω confusion; ην↔ης, οι↔αι sequences |
| **Accent-Based** | `check_grave_accents.py` | Misplaced grave accents on non-ultimate syllables (acute→grave transcription errors) |
| **Multiple Accent** | `check_multiple_accents.py` | OCR-merged words where two words were combined but both retained accents |
| **Missing Accents** | `check_unaccented_words.py` | Words missing accents (filters out valid enclitics/proclitics and all-caps headings) |

### Potential Future Approaches

| Approach | Error Types | Method |
|----------|-------------|--------|
| **Omission Detection** | Haplography, Homoioteleuton, Homoioarcton, Parablepsis | Detect missing words where adjacent words have similar beginnings/endings |
| **Dittography Detection** | Repeated words/phrases | Find consecutive duplicates not present in reference |
| **Article-Noun Agreement** | Case errors | Verify article case matches nearby noun ending |

## Requirements

- Python 3.x
- No external dependencies (uses standard library only)

## License

This project is for academic and research purposes, analyzing public domain Septuagint texts.

## Acknowledgments

- Brenton's Septuagint translation
- Rahlfs Septuaginta edition
- Swete's Old Testament in Greek edition

## To Do
[x] Refactor: Move Brenton.tex input file up to root and update all scripts accordingly.
[x] Refactor: Extract Brenton.tex parsing logic into shared `brenton_parser.py` utility.
- [x] The missing_words, and legitimate words files don't have the same number in them, which are different?
[x] Refactor: For check_sequence_errors move line number to the first column
[x] Manual: Validate sequencing errors
[x] Manual: Verify and Fix Grave Errors
    [x] Investigated why merged words weren't detected by typo script - they were matching compound word combinations and being classified as "legitimate variations". Created `check_multiple_accents.py` to detect these.
[x] fix multiple accents
    [x] why did τοῖ not show up from ΠΑΡΑΛΕΙΠΟΜΕΝΩΝ Α 16:42 -> τοι is a valid word in the Rahlf corpus
[x] find multiple words in a row without accents (ΔΑΝΙΗΛ 9:4)
[ ] find all words starting with vowels that lack breathing marks.
[x] Create a list of valid enclitics/proclitics and check accent-less words against that list.
[ ] may not be worth it: words present, but in different order than rahlf and swete
[ ] confirm fixes applied in all books
[ ] apply all corrections one last time to make sure none missed.
[ ] Specific cases
- [ ] ΑΡΙΘΜΟΙ 12:5	εἰν this must have been in rahlf?
- [ ] ΛΕΥΙΤΙΚΟΝ 14:2	ὁ νὁμος	ὁ νὅμος weird breathign mark in wrong spot.
- [ ] ΑΡΙΘΜΟΙ 15:15	νὀμος	νὄμος similar
- [ ] Todo check for breathing marks in wrong spots (not on first or second vowel, following a consonant)
- [ ] 10066	ΒΑΣΙΛΕΙΩΝ Β 11:25	σου εἰν	σου εἳν
[ ] create word counts for each version, and compare them, if a word is off by a lot, its possibly a common error (εἰν probably happens a lot for εἰς comparatively)