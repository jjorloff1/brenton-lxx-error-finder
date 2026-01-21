# Check Breathing Marks

Detects breathing mark errors in the Brenton Septuagint using rule-based detection.

## Purpose

In Greek, breathing marks (smooth ψιλή and rough δασεία) follow specific rules:
- Every word starting with a vowel or diphthong must have a breathing mark
- Initial ρ always takes rough breathing
- Initial υ always takes rough breathing
- Interior double ρρ should have the pattern ῤῥ (smooth + rough)

This script identifies violations of these rules that indicate OCR transcription errors.

## Detection Logic

The script detects five categories of breathing mark errors:

### 1. Missing Breathing Marks
- **Initial vowel without breathing**: Words starting with a vowel that lack a breathing mark
- **Initial diphthong without breathing**: Words starting with αι, αυ, ει, ευ, οι, ου, ηυ, υι where the second vowel lacks breathing
- **Initial ρ without rough breathing**: Words starting with ρ that lack rough breathing (ῥ)
- **Crasis missing breathing**: Known crasis forms that lack their expected breathing mark

### 2. Wrong Breathing Position
- **Breathing on wrong vowel in diphthong**: Breathing on first vowel when it should be on the second letter of an initial diphthong (αι, αυ, ει, ευ, οι, ου, ηυ, υι)
- **Breathing not on first vowel**: Breathing mark appearing on a vowel that isn't the initial vowel

**Note**: A dieresis (¨) on the second vowel indicates the vowels are pronounced separately (not a diphthong), so `Ἀϊ-` is correctly breathing on the Α, not an error.

### 3. Wrong Breathing Type
- **Smooth breathing on initial ρ**: Initial ρ should always have rough breathing (ῥ not ῤ)
- **Smooth breathing on initial υ**: Initial υ should always have rough breathing (ὑ- not ὐ-)

### 4. Interior Rho Errors
- **Interior single ρ with breathing**: A lone ρ inside a word should not have a breathing mark
- **Interior double ρρ without ῤῥ pattern**: Double rho inside a word should have breathing marks (smooth on first, rough on second)
- **Interior double ρρ with wrong pattern**: e.g., ῥῥ (both rough), ῤῤ (both smooth), or only one marked

### 5. Consonant-Initial Words with Breathing (Crasis Detection)
- **Unexpected breathing on consonant-initial word**: Only crasis forms should have breathing marks when starting with a consonant
- **Crasis with wrong form**: Known crasis forms that have incorrect breathing/accenting

## How It Works

1. Loads the crasis allowlist from `../input/crasis_allowlist.txt`
2. Loads Swete and Rahlfs word lists for suggesting corrections
3. Parses each verse from the input .tex file using BrentonParser
4. For each word:
   - Analyzes word start (vowel, diphthong, ρ, or other consonant)
   - Checks for breathing marks and their positions
   - Applies rule-based error detection
   - Looks up suggested corrections in Swete/Rahlfs dictionaries
5. Writes results to TSV output file

## Crasis Forms

Crasis is the contraction of two words (typically καί + vowel-initial word). The crasis allowlist (`../input/crasis_allowlist.txt`) contains known forms like:
- κἀγώ (καί + ἐγώ)
- κἀκεῖ (καί + ἐκεῖ)
- κἀκεῖνος (καί + ἐκεῖνος)
- τἄλλα (τά + ἄλλα)
- τοὔνομα (τό + ὄνομα)

Words matching these patterns are validated for correct breathing; words with breathing on vowels in consonant-initial words that don't match known crasis forms are flagged.

## Usage

```bash
cd check_breathing_marks
python3 check_breathing_marks.py
```

### Options

- `--input PATH` - Path to input .tex file (default: `../input/Brenton.tex`)
- `--crasis-allowlist PATH` - Path to crasis allowlist (default: `../input/crasis_allowlist.txt`)
- `--rahlfs-words PATH` - Path to Rahlfs word list for suggestions (default: `../input/rahlfs_words.csv`)
- `--swete-words PATH` - Path to Swete word list for suggestions (default: `../input/swete_words.csv`)
- `--output PATH` - Output TSV file path (default: `output/breathing_errors.tsv`)

## Output Files

### Main Output: `output/breathing_errors.tsv`

| Column | Description |
|--------|-------------|
| Line Number | Line number in input .tex file |
| Verse Reference | e.g., "ΓΕΝΕΣΙΣ 1:1" |
| Word | The word with the breathing error |
| Suggested Fix | Correct form from Swete/Rahlfs (if found) |
| Error Type | Category of error detected |
| Full Line | Complete line from source file |

### Error Types

| Error Type | Description |
|------------|-------------|
| `missing_breathing_vowel` | Initial vowel missing breathing mark |
| `missing_breathing_diphthong` | Initial diphthong missing breathing on second vowel |
| `missing_rough_on_rho` | Initial ρ missing rough breathing |
| `breathing_wrong_vowel_diphthong` | Breathing on first vowel of diphthong (should be second) |
| `breathing_not_on_first_vowel` | Breathing on wrong vowel position |
| `smooth_on_initial_rho` | Initial ρ has smooth breathing (should be rough) |
| `smooth_on_initial_upsilon` | Initial υ has smooth breathing (should be rough) |
| `single_interior_rho_with_breathing` | Single interior ρ has breathing mark |
| `double_rho_no_breathing` | Interior ρρ missing breathing marks |
| `double_rho_wrong_pattern` | Interior ρρ has wrong pattern (not ῤῥ) |
| `double_rho_partial_breathing` | Interior ρρ has only one breathing mark |
| `crasis_missing_breathing` | Known crasis form missing breathing |
| `crasis_wrong_form` | Known crasis form has wrong breathing/accenting |
| `unexpected_breathing_consonant_initial` | Consonant-initial word has breathing (not a known crasis) |

## Example Errors Detected

- `ηνίκα` → `ἡνίκα` (missing breathing on initial vowel)
- `Ετι` → `Ἔτι` (missing breathing on initial vowel)
- `επὶ` → `ἐπὶ` (missing breathing on initial vowel)
- `Ἀϊὲ` → `Αἰὲ` (breathing on wrong vowel of diphthong)
- `Σάῥῥᾳ` → `Σάρρα` (double rho has ῥῥ, should be ῤῥ or plain ρρ)
- `κᾀγὼ` → `κἀγὼ` (crasis form has wrong diacritics)
- `νὁμος` → `νόμος` (breathing on consonant-initial word that isn't crasis)

## Integration

After reviewing the output:
1. Determine the correct forms for flagged words
2. Add corrections to `../word_corrections.tsv`
3. Run `apply_corrections/apply_corrections.py` to apply fixes
