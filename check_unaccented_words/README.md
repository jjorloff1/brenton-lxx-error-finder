# Check Unaccented Words

Detects words with missing accent marks in the Brenton Septuagint using a reference list of valid enclitics and proclitics.

## Purpose

In Greek, most words carry accent marks (acute, grave, or circumflex). However, certain words (enclitics and proclitics) legitimately appear without accents. This script identifies words that are missing accents when they shouldn't be.

## Detection Logic

The script flags the following as errors:

1. **Single unaccented words** that are NOT known enclitics/proclitics (likely missing diacritics)
2. **Pairs of unaccented words** where at least one is NOT an enclitic/proclitic
3. **Three or more consecutive unaccented words** (suspicious regardless of word type)

**Exceptions:**
- **All-caps words** (headings/titles like "ΛΟΓΟΣ ΚΥΡΙΟΥ") are always skipped - they legitimately lack accents
- Pairs where both words are valid enclitics/proclitics are written to a separate file for manual review

## How It Works

1. Loads the list of valid enclitics/proclitics from `../input/enclitics_proclitics.txt`
2. Parses each verse from `Brenton.tex`
3. Skips all-caps words entirely (headings/titles)
4. For each unaccented word or sequence:
   - Checks if words are in the valid enclitic/proclitic list
   - Classifies as error, enclitic pair (for review), or OK
5. Writes results to appropriate output files

## Enclitics and Proclitics

The reference file `../input/enclitics_proclitics.txt` contains ~100 valid unaccented forms:

**Proclitics** (lean forward onto following word):
- Articles: ὁ, ἡ, οἱ, αἱ
- Prepositions (full): εἰς, ἐκ, ἐν, ἐπί, πρός, ἀπό, μετά, παρά, κατά, διά, ὑπό, ἀντί, περί, πρό, ἀνά
- Prepositions (elided): ἐπ, μετ, ἀπ, παρ, κατ, δι, ὑπ, ἀντ, περ, πρ, ἀν
- Prepositions (before rough breathing): ἐφ, μεθ, ἀφ, καθ, ὑφ, ἀνθ
- Conjunctions: εἰ, ὡς, ἀλλά, οὐδέ, μηδέ (and elided: ἀλλ, οὐδ, μηδ, δ)
- Negation: οὐ, οὐκ, οὐχ, μή, μήτε

**Enclitics** (lean back onto preceding word):
- Personal pronouns: μου, μοι, με, σου, σοι, σε, οὗ, οἷ, ἕ
- Indefinite pronoun τις/τι (all case forms)
- Present indicative of εἰμί and φημί (except εἶ and φῄς)
- Particles: γε, τε, τοι, περ (and elided: τ)
- Indefinite adverbs: που, ποτε, πως, etc.

## Usage

```bash
cd check_unaccented_words
python3 check_unaccented_words.py
```

### Options

- `--input PATH` - Path to input .tex file (default: `../input/Brenton.tex`)
- `--enclitics PATH` - Path to enclitics/proclitics list (default: `../input/enclitics_proclitics.txt`)
- `--rahlfs-words PATH` - Path to Rahlfs word list for suggested fixes (default: `../input/rahlfs_words.csv`)
- `--swete-words PATH` - Path to Swete word list for suggested fixes (default: `../input/swete_words.csv`)
- `--output PATH` - Main output TSV path (default: `output/unaccented_sequences.tsv`)
- `--enclitic-pairs-output PATH` - Enclitic pairs TSV (default: `output/consecutive_enclitics.tsv`)

## Output Files

### Main Output: `output/unaccented_sequences.tsv`

Contains definite issues requiring correction:

| Column | Description |
|--------|-------------|
| Line Number | Line number in Brenton.tex |
| Verse Reference | e.g., "ΔΑΝΙΗΛ 9:4" |
| Unaccented Words | Words without accents (space-separated) |
| Suggested Fix | Predicted correct form from Rahlfs/Swete (preserves capitalization) |
| Sequence Length | Number of words in sequence |
| Reason | Why flagged: "unknown unaccented word", "non-enclitic in pair: X", or "3+ consecutive unaccented" |
| Context Before | Previous accented word |
| Context After | Next accented word |
| Full Line | Complete line from source file |

The "Suggested Fix" column is populated by looking up each unaccented word (stripped of diacritics) in the Rahlfs and Swete word lists. If found, the properly accented form is suggested. Enclitics/proclitics are left unchanged (they're valid without accents). Words not found in either reference list show the original form unchanged.

### Secondary Output: `output/consecutive_enclitics.tsv`

Contains pairs of consecutive valid enclitics/proclitics for manual review. Same columns as main output. These may be legitimate but warrant inspection for unusual patterns (e.g., two personal pronouns adjacent).

## Example Errors Detected

- `παιδων` → should be `παίδων` (genitive plural, needs accent)
- `αὐτου` → should be `αὐτοῦ` (genitive, needs accent)
- `και` → should be `καί` (conjunction, needs accent)
- `ὁτι` → should be `ὅτι` (conjunction, needs accent and breathing)

## Integration

After reviewing the output:
1. Determine the correct accented forms
2. Add corrections to `../word_corrections.tsv`
3. Run `apply_corrections/apply_corrections.py` to apply fixes
