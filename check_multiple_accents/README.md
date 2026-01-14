# Check Multiple Accents

Detects words in Brenton's Septuagint that have multiple accents, which typically indicates an OCR error where two words were merged together.

## How It Works

Greek words normally have at most one accent (acute, grave, or circumflex). When OCR software merges two words due to a missing space, both words often retain their accents, resulting in a single "word" with multiple accents.

### Detection Logic

1. **3+ accents**: Always flagged (impossible in valid Greek)
2. **Exactly 2 accents**: Flagged unless the following word has no accent

The check for the following word filters out valid **enclisis** cases, where an enclitic word (like `ἐστι`, `τις`) transfers its accent to the preceding word.

### Valid vs Invalid Examples

| Word | Following Word | Status | Reason |
|------|----------------|--------|--------|
| `πολλαὶγίνονται` | `ἁμαρτίαι` (has accent) | **Flagged** | OCR merge error |
| `Εὐποίησον` | `εὐσεβεῖ` (has accent) | Not flagged | Only 1 accent in word |
| Word with 2 accents | `τι` (no accent) | Not flagged | Valid enclisis |

## Usage

```bash
cd check_multiple_accents
python check_multiple_accents.py
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | `../input/Brenton.tex` | Path to input .tex file |
| `--output` | `output/multiple_accents.tsv` | Path to output TSV file |

## Output

The script produces a TSV file with the following columns:

| Column | Description |
|--------|-------------|
| Line Number | Line number in Brenton.tex |
| Verse Reference | e.g., `ΠΑΡΟΙΜΙΑΙ ΣΑΛΩΜΩΝΤΟΣ 29:16` |
| Word | The word with multiple accents |
| Following Word | The next word in the verse (if any) |
| Following Word Has Accent | Yes/No/N/A |
| Accent Count | Number of accents found (2, 3, etc.) |
| Accent Positions | Position and type of each accent |
| Full Line | Complete line for context |

## Example

```
Line Number  Verse Reference                    Word              Following Word  ...
21897        ΠΑΡΟΙΜΙΑΙ ΣΑΛΩΜΩΝΤΟΣ 29:16        πολλαὶγίνονται    ἁμαρτίαι        ...
```

This word should be corrected to `πολλαὶ γίνονται` (with a space).

## Integration

Words detected by this script are likely OCR errors that should be:
1. Reviewed manually to confirm the missing space
2. Added to `word_corrections.tsv` with the corrected form
3. Applied using the `apply_corrections` scripts
