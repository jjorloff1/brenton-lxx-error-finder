# Check Sequence Errors

Detects OCR sequence errors in Brenton's Septuagint by performing word-by-word alignment against the Rahlfs edition.

## Purpose

This script complements `check_missing_words_for_typos` by catching errors that pass vocabulary checks but are wrong in context. For example, both `-ου` and `-ον` endings can be valid Greek, but only one is correct for a given word form.

## Error Types Detected

### Single Character Confusions
These characters can be visually confused by OCR and produce valid Greek words:

**υ/ν/ς/σ group:**
- `υ` ↔ `ν` (e.g., `-ου` vs `-ον`, `-υν` vs `-ων`)
- `υ` ↔ `ς`
- `ν` ↔ `ς`
- `ς` ↔ `σ` (final vs medial sigma)

**ε/η pair:**
- `ε` ↔ `η` (e.g., `μέν` vs `μήν`, `δέ` vs `δή` - common particles)

**ο/ω pair:**
- `ο` ↔ `ω` (e.g., `λύομεν` vs `λύωμεν` - indicative vs subjunctive)

### Multi-Character Sequence Confusions
- `ην` ↔ `ης` (e.g., accusative vs genitive endings)
- `οι` ↔ `αι` (e.g., dative plural `-οις` vs `-αις`)

## Usage

```bash
cd check_sequence_errors
python3 check_sequence_errors.py
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--brenton` | `../check_missing_words_for_typos/input/Brenton.tex` | Path to Brenton source |
| `--rahlfs-words` | `../check_missing_words_for_typos/input/rahlfs_words.csv` | Rahlfs word list |
| `--rahlfs-versification` | `../check_missing_words_for_typos/input/rahlfs_versification.csv` | Rahlfs verse mappings |
| `--accepted-words` | `../accepted_words.txt` | Words to skip |
| `--corrections` | `../word_corrections.tsv` | Already-corrected words to skip |
| `--accepted-variants` | `../accepted_sequence_variants.tsv` | Verse-specific accepted variants |
| `--output` | `output/sequence_errors.tsv` | Output file for detected errors |
| `--mismatches-output` | `output/versification_mismatches.tsv` | Log of verse alignment issues |

## Output Files

### `sequence_errors.tsv`
Tab-separated file with columns:
- Verse Reference
- Line Number
- Brenton Word
- Rahlfs Word
- Error Type (`single_char` or `sequence`)
- Context (e.g., `-ου → -ον`)
- Full Line

### `versification_mismatches.tsv`
Log of verses that couldn't be aligned between Brenton and Rahlfs:
- Brenton Reference
- Rahlfs Reference
- Status (`not_found` or `conversion_failed`)
- Line Number

## Algorithm

1. For each verse in Brenton:
   - Convert reference to Rahlfs format
   - Get ordered word lists from both sources
   - Align word sequences using `difflib.SequenceMatcher`

2. For each aligned word pair where words differ:
   - Skip if word is in `accepted_words.txt` or `word_corrections.tsv`
   - Check for single-character υ/ν/ς/σ confusion
   - Check for sequence confusion (ην↔ης, οι↔αι)
   - Apply accent-based filtering (see below)
   - Record matches with context information

## Accent-Based Filtering

To reduce false positives, the script filters out word pairs where accent differences suggest a valid textual variant rather than an OCR error.

### Filtering Logic
- **Different accent position**: Filtered (likely valid Brenton variant)
- **Different type involving circumflex**: Filtered (likely valid Brenton variant)
- **Same accent position and type**: Kept for review (may be transcription error)
- **Same position, acute/grave switch**: Kept (acute and grave are essentially the same accent)
- **Brenton missing accent, Rahlfs has one**: Kept (accent-bearing character may have been mistranscribed)

### Example
| Brenton | Rahlfs | Accents | Action |
|---------|--------|---------|--------|
| αὐτὸν | αὐτοῦ | grave on ο vs circumflex on υ | Filtered |
| τὴς | τὴν | both grave on η | Kept |

## Accepting Variants

Unlike `accepted_words.txt` which accepts words globally, sequence variants need to be accepted on a **case-by-case basis** because common words like `τὴς`/`τὴν` appear many times and may be correct in some verses but wrong in others.

### `accepted_sequence_variants.tsv`

Located at project root. Format:
```
Verse Reference<tab>Brenton Word<tab>Rahlfs Word
```

Example:
```
ΓΕΝΕΣΙΣ 3:8	τὴς	τὴν
ΓΕΝΕΣΙΣ 3:8	φωνὴς	φωνὴν
```

This accepts specific verse+word combinations as intentional textual differences (not OCR errors).

## Integration with Existing Workflow

After running this script:
1. Review `sequence_errors.tsv` for true positives
2. For **OCR errors**: Add corrections to `../word_corrections.tsv`
3. For **valid textual variants**: Add to `../accepted_sequence_variants.tsv`
4. Re-run the script to verify errors are filtered
5. Run `../apply_corrections/apply_corrections.py` to apply fixes
