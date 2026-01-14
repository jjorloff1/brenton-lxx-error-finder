# Check Grave Accents

Detects misplaced grave accents in Brenton's Septuagint text.

## Purpose

In Greek, the grave accent (`) should only appear on the **ultimate syllable** (the last vowel) of a word. It replaces the acute accent when the word is followed by another word in continuous speech.

A grave accent appearing on any vowel other than the last is a likely transcription error - the original text probably had an acute (´) that was mistakenly rendered as a grave.

## How It Works

The script:
1. Scans through Brenton.tex extracting Greek words
2. For each word, identifies all accents using Unicode decomposition
3. Finds the position of the last vowel (α, ε, η, ι, ο, υ, ω)
4. Flags words where a grave accent appears on a vowel **before** the last vowel

## Usage

```bash
cd check_grave_accents
python3 check_grave_accents.py
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | `../input/Brenton.tex` | Path to input .tex source |
| `--output` | `output/misplaced_graves.tsv` | Output file path |

## Output

### `misplaced_graves.tsv`

Tab-separated file with columns:
- **Verse Reference**: Full verse identifier (e.g., "ΓΕΝΕΣΙΣ 1:1")
- **Line Number**: Line in Brenton.tex where error found
- **Word**: The word containing the misplaced grave
- **Grave Position**: Character position (0-indexed) of the grave accent
- **Base Char**: The vowel that incorrectly carries the grave
- **Full Line**: Complete LaTeX line for context

## Example

If the text contains `τὴς` where it should be `τῆς` (grave on η instead of circumflex), and the word is followed by more text with a final vowel, this would be flagged.

More commonly, this catches cases where an acute accent was misread as a grave during OCR or transcription, such as:
- `πρὸσωπον` instead of `πρόσωπον` (grave on non-final ο)

## Greek Vowels

The script recognizes these as vowels:
- Lowercase: α, ε, η, ι, ο, υ, ω
- Uppercase: Α, Ε, Η, Ι, Ο, Υ, Ω

## Integration

After finding errors:
1. Review each flagged word in context
2. Determine if the grave should be an acute or circumflex
3. Add corrections to `../word_corrections.tsv`
4. Run `../apply_corrections/apply_corrections.py` to apply fixes
