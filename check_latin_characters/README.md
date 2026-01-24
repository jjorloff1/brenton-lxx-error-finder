# Check Latin Characters

A **correction verification tool** that detects Latin characters incorrectly appearing in Greek words.

## Purpose

When manually entering Greek corrections, it's easy to accidentally type a Latin character that looks identical to its Greek equivalent. For example:
- Latin `K` looks identical to Greek `Κ` (Kappa)
- Latin `Y` looks identical to Greek `Υ` (Upsilon)
- Latin `p` looks identical to Greek `ρ` (rho)
- Latin `A` looks like Greek `Α` (Alpha)

This script scans both the corrected output file (`Brenton-corrected.tex`) and the corrections file (`word_corrections.tsv`), flagging any Greek word that contains Latin characters. This helps catch errors before or after corrections are applied.

## How It Works

The script:
1. Scans through Brenton.tex extracting Greek words (including mixed Latin-Greek words)
2. Scans through word_corrections.tsv checking both original and corrected words
3. For each word, checks every character against a set of confusable Latin characters
4. Flags words containing any Latin characters
5. Generates suggested fixes by replacing Latin characters with their Greek equivalents

## Usage

```bash
cd check_latin_characters
python3 check_latin_characters.py
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | `../input/Brenton-corrected.tex` | Path to corrected .tex file |
| `--corrections` | `../word_corrections.tsv` | Path to word corrections file |
| `--output` | `output/latin_characters.tsv` | Output file path |

## Output

### `latin_characters.tsv`

Tab-separated file with columns:
- **Source File**: Which file the error was found in (Brenton.tex or word_corrections.tsv)
- **Line Number**: Line number where error found
- **Verse Reference**: Full verse identifier (e.g., "ΓΕΝΕΣΙΣ 1:1") or "ALL (corrected)" for corrections
- **Word**: The word containing Latin character(s)
- **Suggested Fix**: Word with Latin characters replaced by Greek equivalents
- **Errors Found**: Comma-separated list of Latin characters detected (e.g., "p, A")
- **Full Line**: Complete line for context

## Latin Character Detection

The script detects **all 52 Latin letters** (A-Z, a-z) mixed with Greek text. This catches two types of errors:

### Visually Similar Characters
Characters that look alike and may be confused visually:

| Latin | Greek | Example |
|-------|-------|---------|
| A | Α (Alpha) | Nearly identical |
| B | Β (Beta) | Nearly identical |
| E | Ε (Epsilon) | Nearly identical |
| K | Κ (Kappa) | Nearly identical |
| O | Ο (Omicron) | Nearly identical |
| P | Ρ (Rho) | Nearly identical |
| Y | Υ (Upsilon) | Nearly identical |

### Keyboard Layout Errors
When typing with the wrong keyboard layout active, Latin letters appear instead of Greek. The script maps Latin keys to their Greek keyboard equivalents:

| Latin Key | Greek Letter | Latin Key | Greek Letter |
|-----------|--------------|-----------|--------------|
| a | α (alpha) | n | ν (nu) |
| b | β (beta) | r | ρ (rho) |
| d | δ (delta) | s | σ (sigma) |
| f | φ (phi) | t | τ (tau) |
| g | γ (gamma) | v | ω (omega) |
| h | η (eta) | w | ς (final sigma) |
| k | κ (kappa) | z | ζ (zeta) |
| l | λ (lambda) | ... | ... |
| m | μ (mu) | | |

## Example Errors

**Visual similarity (looks the same):**
- `Kύριος` should be `Κύριος` (Latin 'K' instead of Greek 'Κ')
- `Yἱοὶ` should be `Υἱοὶ` (Latin 'Y' instead of Greek 'Υ')

**Keyboard layout error (wrong language mode):**
- `vμέρα` should be `ὡμέρα` (Latin 'v' typed instead of Greek 'ω')
- `nῦν` should be `νῦν` (Latin 'n' typed instead of Greek 'ν')

## Workflow Integration

**Before applying corrections:**
Run this script to check `word_corrections.tsv` for Latin characters before they propagate to the corrected file.

**After applying corrections:**
Run this script against `Brenton-corrected.tex` to verify no Latin characters were introduced.

**When errors are found:**
1. Review each flagged word
2. Fix the Latin character in `word_corrections.tsv` (replace with Greek equivalent)
3. Re-run `apply_corrections.py` to regenerate corrected files
4. Re-run this script to verify the fix
