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
├── README.md                    # This file
├── word_corrections.tsv         # Central corrections file (shared between workflows)
├── find_errors/                 # Error detection scripts and data
│   ├── README.md                # Detailed documentation for error finding
│   ├── check_missing_words.py   # Main error detection script
│   ├── input/                   # Source files (Brenton.tex, reference CSVs)
│   ├── output/                  # Analysis results (missing_words*.tsv)
│   └── logs/                    # Execution logs
├── apply_corrections/           # Correction application scripts
│   ├── README.md                # Detailed documentation for applying corrections
│   ├── apply_corrections.py     # Script to apply corrections to LaTeX
│   ├── grcbrent_xetex_original/ # Original LaTeX source files
│   └── grcbrent_xetex_corrected/# Corrected LaTeX output files
└── contributor_analysis/        # Files for manual verification by contributors
```

## Quick Start

### Find Errors
```bash
cd find_errors
python3 -u check_missing_words.py |& tee "logs/script_run-$(date +%s).log"
```
Results are written to `find_errors/output/`.

### Apply Corrections
```bash
cd apply_corrections
python3 apply_corrections.py
```
Corrected files are written to `apply_corrections/grcbrent_xetex_corrected/`.

## Workflow

### 1. Find Errors (`find_errors/`)

The `check_missing_words.py` script:
- Reads the Brenton Greek text (`input/Brenton.tex`)
- Compares each word against Rahlfs and Swete word lists
- Identifies words not found in either reference edition
- Performs typo detection using similarity matching
- Generates output files categorizing potential errors

Key outputs:
- `missing_words_likely_typos.tsv` - High-confidence typos for review
- `missing_words_legitimate_variations.tsv` - Valid spelling differences
- `missing_words_unmatched.tsv` - Words needing manual review

### 2. Document Corrections (`word_corrections.tsv`)

After reviewing the error detection output, add corrections to `word_corrections.tsv`:
- Tab-separated format: `Verse Reference<tab>Incorrect Word<tab>Correct Word`
- Example: `ΓΕΝΕΣΙΣ 5:10	ἑπτκόσια	ἑπτακόσια`
- Use `ALL` for verse reference to apply correction globally

This file is shared between both workflows - errors found by `find_errors/` are corrected via entries here, and `apply_corrections/` reads this file to apply the fixes.

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
- Is read by `find_errors/` to skip already-corrected words
- Is read by `apply_corrections/` to apply fixes to source files

### Reference Data
Located in `find_errors/input/`:
- `rahlfs_words.csv` / `swete_words.csv` - Word lists from reference editions
- `rahlfs_versification.csv` / `swete_versification.csv` - Verse mappings
- `accepted_words.txt` - Manually verified acceptable variations

## Additional Folders

### `contributor_analysis/`
Contains files for the manual verification process used by project contributors to help validate corrections. Not used by any scripts.

## Requirements

- Python 3.x
- No external dependencies (uses standard library only)

## License

This project is for academic and research purposes, analyzing public domain Septuagint texts.

## Acknowledgments

- Brenton's Septuagint translation
- Rahlfs-Hanhart Septuaginta edition
- Swete's Old Testament in Greek edition
