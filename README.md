# Brenton LXX Error Finder

A Python tool to identify potential errors and discrepancies in Brenton's Septuagint (LXX) text by comparing it against the Rahlfs and Swete editions.

## Purpose

This repository contains scripts to analyze the Greek text of Brenton's English Septuagint edition (`Brenton.tex`) and identify words that don't appear in two authoritative Septuagint editions:
- **Rahlfs Edition** (rahlfs_words.csv, rahlfs_versification.csv)
- **Swete Edition** (swete_words.csv, swete_versification.csv)

The tool helps identify:
- **Typographical errors** (typos with high similarity to known words)
- **OCR errors** (from scanning physical texts)
- **Proper names** (not always in word lists)
- **Number words** (may vary between editions)
- **Accepted variations** (maintained in accepted_words.txt)

The script performs verse-specific checking, looking first in the exact verse, then in surrounding verses (±2 verses), and finally in the broader corpus to identify likely typos with high confidence.

## Project Structure

```
.
├── Brenton.tex                      # Source text with Greek Septuagint (LaTeX format)
├── book_code_mappings.py            # Mappings between Greek book names and edition codes
├── check_missing_words.py           # Main analysis script
├── compare-brenton-swete.py         # Additional comparison script
├── accepted_words.txt               # Manually verified words to skip
├── word_corrections.tsv             # Previously identified errors and their corrections
├── rahlfs_words.csv                 # Word list from Rahlfs edition
├── rahlfs_versification.csv         # Verse reference mappings (Rahlfs)
├── swete_words.csv                  # Word list from Swete edition
├── swete_versification.csv          # Verse reference mappings (Swete)
├── missing_words.tsv                # Output: all missing words
├── missing_words_typo_check.tsv     # Output: full analysis with flags
├── missing_words_likely_typos.tsv   # Output: filtered likely typos
└── logs/                            # Execution logs
```

## Requirements

- Python 3.x
- No external dependencies (uses standard library only)

## Installation

Clone this repository:

```bash
git clone https://github.com/jjorloff1/brenton-lxx-error-finder.git
cd brenton-lxx-error-finder
```

## Usage

### Basic Usage

Run the script with typo checking enabled (default):

```bash
python3 -u check_missing_words.py |& tee "logs/script_run-${EPOCHREALTIME}.log"
```

This command:
- Runs the script unbuffered (`-u`) for real-time output
- Captures both stdout and stderr (`|&`)
- Saves output to a timestamped log file in the `logs/` directory
- Displays output in the terminal simultaneously (`tee`)

### Command-Line Options

```bash
# Run without typo checking (faster):
python3 check_missing_words.py --no-typo-check

# Specify custom input files:
python3 check_missing_words.py --bible MyBible.tex --rahlfs my_rahlfs.csv

# See all options:
python3 check_missing_words.py --help
```

Available options:
- `--bible` - Path to Bible .tex file (default: Brenton.tex)
- `--rahlfs` - Path to Rahlfs words CSV (default: rahlfs_words.csv)
- `--swete` - Path to Swete words CSV (default: swete_words.csv)
- `--rahlfs-versification` - Path to Rahlfs versification CSV (default: rahlfs_versification.csv)
- `--swete-versification` - Path to Swete versification CSV (default: swete_versification.csv)
- `--output` - Path to output TSV file (default: missing_words.tsv)
- `--accepted-words` - Path to accepted words file (default: accepted_words.txt)
- `--no-typo-check` - Disable typo checking for faster processing

## Output Files

The script generates three output files:

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
- Area Match? (Found within ±2 verses)

### 3. `missing_words_likely_typos.tsv`
Filtered list containing only probable typos (excluding proper names and numbers):
- Focus on words with ≥85% similarity to known words
- Prioritizes verse-specific matches
- Ideal starting point for manual review

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
   - Then checks surrounding area (±2 verses)
   - Falls back to broader corpus search
   - Uses sequence matching to find words with ≥85% similarity
   - Flags proper names (capitalized words)
   - Flags number words (contains Greek number patterns)

4. **Output Generation**
   - Writes results to TSV files
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

The `accepted_words.txt` file contains words that have been manually verified as correct variations or acceptable differences. Words in this file are skipped during processing. Format:
- One word per line
- Lines starting with `#` are comments
- Words should match the normalized form (lowercase, diacritics stripped)

## Word Corrections

The `word_corrections.tsv` file tracks previously identified and corrected errors. This file allows the script to skip words that have already been examined and corrected, preventing duplicate work. Format:
- Tab-separated values (TSV)
- Three columns: Verse Reference, Incorrect Word, Corrected Word
- Example: `ΓΕΝΕΣΙΣ 5:10	ἑπτκόσια	ἑπτακόσια`
- Special entries can use `ALL` for verse reference to apply across all verses

To add corrections:
1. Review output files (especially `missing_words_likely_typos.tsv`)
2. Verify the error and identify the correct word
3. Add entry to `word_corrections.tsv` in the format: `verse_ref	incorrect_word	correct_word`
4. Rerun the script to skip already-corrected words

## Contributing

To add accepted words:
1. Review output files (especially `missing_words_likely_typos.tsv`)
2. Verify words manually against source texts
3. Add verified words to `accepted_words.txt`
4. Rerun the script to update output

## License

This project is for academic and research purposes, analyzing public domain Septuagint texts.

## Acknowledgments

- Brenton's Septuagint translation
- Rahlfs-Hanhart Septuaginta edition
- Swete's Old Testament in Greek edition
