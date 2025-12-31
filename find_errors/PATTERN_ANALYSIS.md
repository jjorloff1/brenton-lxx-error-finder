# Pattern Analysis: Brenton LXX Word Variations and Transcription Errors

## Summary
This document contains patterns identified from analyzing:
- **word_corrections.tsv** (69 transcription errors)
- **accepted_words.txt** (154 legitimate Brenton spelling variations)
- **missing_words_likely_typos.tsv** (for context matching)

---

## PART 1: TRANSCRIPTION ERROR PATTERNS
*Source: word_corrections.tsv*

These are OCR/transcription errors that should be corrected in the Brenton text.

### 1. Character Substitution Errors (Most Common)

#### High Frequency Substitutions:
- **ν ↔ υ** (9 total occurrences)
  - `ν → υ`: 6 times
  - `υ → ν`: 3 times
  - *Example*: `ὑποχρίνου` → `ὑποχρίνοv`

- **ξ → ζ** (3 occurrences)
  - *Example*: `ἔξησε` → `ἔζησε`, `ἔξησεν` → `ἔζησεν`

- **ν ↔ ς** (5 occurrences)
  - `ν → ς`: 3 times
  - `ς → ν`: 2 times
  - *Example*: `αὐτοὺδ` → `αὐτοὺς` (d mistaken for ς)

#### Medium Frequency:
- **ε → ω** (2 occurrences)
  - *Example*: `γενν-` forms

- **φ → θ** (2 occurrences)
  - *Example*: `ὑπελείφη` → `ὑπελείφθη`

#### Single Occurrences:
- **ο → σ** (1): Visual similarity in Greek script
- **α → σ** (1): Similar issue
- **γ → Y** (1): Capital gamma confused with Y
- **π → κ**: OCR confusion
- **π → ρ**: Visual similarity
- **μ → ψ**: Complex character confusion
- **ο → ι**: Vowel confusion
- **ι → ν**: Character similarity

### 2. Insertion Errors (Missing Characters)
*Pattern: Correct word has MORE characters than transcribed*

Common patterns:
- **Missing vowels in middle of words**
  - `ἑπτκόσια` → `ἑπτακόσια` (missing α)
  - `ἐνατίον` → `ἐναντίον` (missing ν)
  - `ἀγαπτοῦ` → `ἀγαπητοῦ` (missing η)

- **Missing consonants**
  - `ἀδφή` → `ἀδελφή` (missing ελ)
  - `τερέινθον` → `τερέβινθον` (missing β)

- **Missing verb endings/particles**
  - `ποιήεις` → `ποιήσεις` (missing σ)
  - `ὑπελείφη` → `ὑπελείφθη` (missing θ)

### 3. Deletion Errors (Extra Characters)
*Pattern: Transcribed word has MORE characters than correct*

Common patterns:
- **Extra final letters**
  - `ὑπήκουσελ` → `ὑπήκουσε` (extra λ)
  - `ἦσανς` → `ἦσαν` (extra ς)
  - `ῥομφαίανν` → `ῥομφαίαν` (extra ν)
  - `περιστόμιονν` → `περιστόμιον` (extra ν)

- **Doubled vowels/diacritics**
  - `ἐρχομενεην` → `ἐρχομένην`
  - `πάσηῃ` → `πάσῃ`
  - `σεε` → `σε`

### 4. Transposition Errors (Swapped Characters)

- `συνέκριεν` → `συνέκρινε` (εν ↔ νε)
- `ἐξήθλοσάν` → `ἐξήλθοσάν` (θλ ↔ λθ)
- `δοξασθήοσμαι` → `δοξασθήσομαι` (οσ ↔ σο)

---

## PART 2: LEGITIMATE BRENTON SPELLING VARIATIONS
*Source: accepted_words.txt*

These are legitimate Ancient Greek textual variants that appear in Brenton but differ from Rahlfs/Swete.

### 1. Lambda Future Forms (λήψ- vs λημψ-)
**Pattern**: Future tense of λαμβάνω and compounds
**Category**: Morphological variation (both forms are attested in Greek)

Examples (28 words):
- `λήψομαι, λήψονται`
- `ἀναλήψεται, ἀναλήψεσθε`
- `ἀντιλήψῃ, ἀντιλήψεται, ἀντιλήψομαι, ἀντιλήψονταί, ἀντιλήψεις`
- `ἐπιλήψεται, ἐπιλήψονται`
- `καταλήψεται, καταλήψομαι, καταλήψῃ`
- `περιλήψεταί, περιλήψεως`
- `προκαταλήψῃ`
- `συλλήψεται, συλλήψῃ, συλλήψει, συλλήψονται, συλλήψεως, συλλήψεων`
- `συμπεριλήψῃ`
- `συναντιλήψεται, συναντιλήψονταί`
- `ὑπολήψομαι`
- `μεταλήψεσθαι`

**Linguistic Note**: Both λήψομαι and λήμψομαι are valid future forms in different dialects/periods.

### 2. Aorist Passive Forms (λήφθη vs λήμφθη)
**Pattern**: Aorist passive of λαμβάνω
**Category**: Morphological variation

Examples:
- `ἐλήφθη` (aorist passive 3rd singular)
- `συμπαραληφθῇς`

### 3. Destruction Verbs (ὀλοθρ- vs ὀλεθρ-)
**Pattern**: Verbal root variation
**Category**: Textual variant (both forms exist in manuscripts)

Examples:
- `ἐξολοθρεύσω` vs standard `ἐξολεθρεύσω`
- Related: `ἐξωλοθρεύθη`

**Linguistic Note**: Both ὀλοθρεύω and ὀλεθρεύω appear in Greek texts.

### 4. Loan Verbs (δανε- vs δανι-)
**Pattern**: Present stem vowel variation
**Category**: Dialectal/manuscript variation

Examples from likely_typos:
- `δανειεῖς, δανειῇ` vs `δανιεῖς, δανιῇ`

### 5. Generation/Produce Words (γενν- vs γενη-)
**Pattern**: Double-nu vs single-nu with eta
**Category**: Orthographic variation

Examples:
- `γεννήματι, γεννημάτων` vs `γενήματος, γενημάτων`
- `γέννημα`

### 6. Command Verbs (ἐντέλλ- variations)
**Pattern**: Command/enjoin verb forms
**Category**: Morphological variation

From likely_typos:
- `ἐντλλομαι` vs `ἐντέλλομαί`
- `ἀντέλλομαί` vs `ἐντέλλομαί`

### 7. Circumcision Verbs
**Pattern**: Infinitive forms
**Category**: Morphological variation

Examples:
- `περιτεμέσθαι` vs `περιτεμνεσθαι`

### 8. Compound Verb Variations (21+ words)
**Pattern**: Various compound verbs with prefix variations
**Category**: Prepositional prefix variations, aspectual differences

Examples:
- `ἀναστρέψομεν, ἀποκριθεῖσαι, ἀποκυλίσουσι`
- `ἐξαιρέσεως, ἐξηλείφησαν, ἐξωλοθρεύθη`
- `καταστῆναι, καταλείπετε, καταλειπέτω`
- `συντετελέκατε, συνιδωτὸν`
- `ἀποτεκνωθῶ, ἀποκατέστησε, ἀποστέλλῃς`

### 9. Vowel Variations/Contractions (19+ words)
**Pattern**: Vowel lengthening, contraction, or ablaut
**Category**: Phonological/dialectal variation

Examples:
- **Circumflex endings**: `εὐώδωκε, εὐώδωσε`
- **Diphthong variations**: `ἀρέσκοι, κακώσωμεν`
- **Vowel quality**: `γινώσκον, χαλαβώτης`
- **Participial forms**: `ἐμπορευόμενοι, ἐναρχόμενοι`
- **Aorist forms**: `ἀφείλετο, ἀφείλοντο, περιείλετο, προείλετο`

### 10. Other Notable Variations (79+ words)
**Pattern**: Miscellaneous legitimate variants

Including:
- **Drachma spellings**: `δίδραγμα` (double-drachma)
- **Jewelry terms**: `ψέλλια` (bracelets)
- **Compound nouns**: `ἀδελφιδοῦν` (nephew)
- **Technical terms**: `σφυρωτῆρος` (shoe-latchet)
- **Rare verb forms**: `κατεβιάσατο, χρᾶσθε, ἐσπούδαζον`
- **Participles**: `ὑπολείπεσθε, ἐναπεποιημένης`

### 11. Known Transcription Issues in Brenton
**Pattern**: Systematic transcription errors

Examples:
- `γἱοὶ` → should be `υἱοὶ` (sons) - systematic OCR error
- `νἱῶν` → should be `υἱῶν` (of sons)
- `μον` → often should be `μου` (my)
- `λέγεν` → appears as variant of `λέγων` (saying)

---

## DETECTION STRATEGY RECOMMENDATIONS

### For Transcription Errors (Should be Flagged):
1. **High confidence**: ν/υ substitutions, ξ/ζ substitutions
2. **Medium confidence**: Doubled final letters (νν, ςς), obvious transpositions
3. **Context-dependent**: Missing vowels in middle of words (check against reference)

### For Legitimate Variations (Should NOT be Flagged):
1. **Lambda futures**: Any word matching `.*λήψ.*` or `.*λημψ.*` pattern
2. **Destruction verbs**: `.*ολοθρ.*` or `.*ολεθρ.*`
3. **Generation words**: `.*γενν.*` with eta variations
4. **Compound variations**: Long words (8+ chars) with standard prefixes (ἀνα-, ἀπο-, κατα-, ἐπι-, ἐξ-, συν-)

### Confidence Scoring:
- **Very likely error** (>95%): Character substitutions from high-frequency list + short edit distance
- **Likely error** (85-95%): Patterns matching transcription error types
- **Possible variation** (85-90%): Matches compound verb or vowel variation patterns
- **Likely variation** (<85%): Matches lambda future, destruction verb, or generation word patterns

