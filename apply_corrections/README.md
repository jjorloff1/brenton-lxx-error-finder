# Apply Corrections Script

This script applies text corrections from `word_corrections.tsv` to Greek Septuagint LaTeX source files, producing corrected output files and a detailed log.

## Quick Start

```bash
cd apply_corrections
python3 apply_corrections.py
```

**Input:**
- `../word_corrections.tsv` - Tab-separated corrections file (in parent directory)
- `grcbrent_xetex_original/` - Source LaTeX files (53 books)

**Output:**
- `grcbrent_xetex_corrected/` - Corrected LaTeX files
- `grcbrent_xetex_corrected/correction_log.txt` - Detailed change log

---

## How It Works

### 1. Correction Categories

The script processes three types of corrections from the TSV file:

| Category | Description | Example |
|----------|-------------|---------|
| **Specific** | Target a specific book and verse | `ΓΕΝΕΣΙΣ 14:22  Κύπιον  Κύριον` |
| **ALL** | Apply to all files globally | `ALL  μον  μου` |
| **Diacritical** | Last 7 ALL entries - fix breathing marks | `ALL  ʼΙ  Ἰ` |

**Processing Order:**
1. Specific corrections for each book (sorted by length, longest first)
2. ALL corrections (excluding last 7)
3. Diacritical corrections (last 7 ALL entries)

### 2. Why Sort by Length?

Corrections are sorted longest-first to prevent substring corruption:

```
Problem: If "ἐγ" → "ἐν" runs before "ἐγαπημένον" → "ἠγαπημένον"
         The word becomes "ἐναπημένον" (corrupted!)

Solution: Process longer strings first, so "ἐγαπημένον" is corrected
          before "ἐγ" has a chance to match inside it.
```

---

## Word Boundary Logic

### The Problem

Simple string replacement causes false matches:

| Correction | Intended Target | False Match | Result |
|------------|-----------------|-------------|--------|
| `μον` → `μου` | standalone "μον" | `πόλεμον` | `πόλεμου` (wrong!) |
| `ἔτου` → `ἔτους` | typo "ἔτου" | `ἔτους` | `ἔτουςς` (double sigma!) |

### The Solution

The script requires **both start AND end word boundaries** for all corrections:

```python
# A match is valid only if:
# 1. Preceded by non-Greek-letter (space, punctuation, start of text)
# 2. Followed by non-Greek-letter (space, punctuation, end of text)
```

### Exceptions

**Diacritical fixes** (`ʼΑ` → `Ἀ`, `ʼΙ` → `Ἰ`, etc.):
- Only require START boundary
- These are always at word starts, followed by more letters
- Example: `ʼΙεζραῒα` → `Ἰεζραῒα`

**Strings with embedded spaces** (like ` ὕξ `):
- The spaces in the string itself serve as boundaries
- No additional boundary check needed where space exists

---

## Greek Character Detection

The script identifies Greek letters using Unicode ranges:

| Range | Name | Characters |
|-------|------|------------|
| U+0370–U+03FF | Greek and Coptic | α, β, γ, Α, Β, Γ, etc. |
| U+1F00–U+1FFF | Greek Extended | ἀ, ἁ, ᾶ, etc. (with diacritics) |

**Important:** The modifier letter apostrophe `ʼ` (U+02BC) is **NOT** treated as a Greek letter. It's punctuation that appears before capital letters in the source text and gets replaced with proper breathing marks.

---

## Understanding the Log File

### Structure

```
================================================================================
CORRECTION LOG
================================================================================

Total corrections applied: 771
Corrections not found: 2
Corrections at unexpected locations: 3

--------------------------------------------------------------------------------
SUCCESSFUL CORRECTIONS
--------------------------------------------------------------------------------

File: GEN_src.tex, Line 375
  TSV Line: 1
  Reference: ΓΕΝΕΣΙΣ 14:22
  Changed: 'Κύπιον' -> 'Κύριον'
  Location: Chapter 14, Verse 22

...
```

### "Not Found" Entries

These usually indicate **duplicate corrections** in the TSV:

```
TSV Line 238: ΒΑΣΙΛΕΙΩΝ Δ 22:1
  Looking for: 'θυλάτηρ'
```

If the same typo appears at two verses (e.g., line 220 for verse 9:34 and line 238 for verse 22:1), the first correction fixes **all** occurrences, leaving nothing for the second.

### "Unexpected Location" Entries

The correction was applied, but at a different verse than the TSV specified:

```
Location: Chapter 1, Verse 31 [UNEXPECTED: expected 1:30, found at 1:31]
```

This happens when:
- The typo appears in multiple verses
- Verse boundaries in the source differ slightly from the reference

**The correction is still applied correctly** - this is just informational.

---

## TSV File Format

The `word_corrections.tsv` file uses tab-separated columns:

| Column | Description | Example |
|--------|-------------|---------|
| 1 | Verse reference (or "ALL") | `ΓΕΝΕΣΙΣ 14:22` |
| 2 | Incorrect text | `Κύπιον` |
| 3 | Correct text | `Κύριον` |
| 4 | Notes (optional) | `rahlf` |

**Special values:**
- `ALL` in column 1 = apply to every file
- Blank lines are ignored
- The last 7 `ALL` entries are treated as diacritical fixes

---

## LaTeX File Structure

The source files use these markers:

| Marker | Purpose | Example |
|--------|---------|---------|
| `\MT` | Book name | `{\MT ΓΕΝΕΣΙΣ` |
| `\ChapOne{1}` | First chapter | |
| `\Chap{N}` | Subsequent chapters | `\Chap{14}` |
| `\PsalmChap{N}` | Psalm chapters | |
| `\OneChap` | Single-chapter books | |
| `\VerseOne{1}` | First verse of chapter | |
| `\VS{N}` | Subsequent verses | `\VS{22}` |

The script extracts Greek book names from `\MT` tags to map them to filenames (e.g., `ΓΕΝΕΣΙΣ` → `GEN_src.tex`).

---

## Troubleshooting

**Script can't find TSV file:**
- Ensure `word_corrections.tsv` exists in the parent directory
- Run from within the `apply_corrections/` folder

**Unexpected corrections or corrupted text:**
- Check if a short string is matching inside longer words
- The word boundary logic should prevent this, but report any issues

**Missing corrections:**
- Check the "not found" section of the log
- May be a duplicate entry or the typo doesn't exist in the source
