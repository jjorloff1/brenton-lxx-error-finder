"""
Book code mappings between Brenton (Greek names), Swete, and Rahlfs editions of the Septuagint.

This module provides dictionaries that map between the Greek book names used in Brenton.tex
and the book codes used in swete_versification.csv and rahlfs_versification.csv.

Usage:
    from book_code_mappings import BRENTON_TO_SWETE, BRENTON_TO_RAHLFS
    
    # Get Swete code for a Brenton book
    swete_code = BRENTON_TO_SWETE.get("ΓΕΝΕΣΙΣ")  # Returns "Gen"
    
    # Get Rahlfs code for a Brenton book  
    rahlfs_code = BRENTON_TO_RAHLFS.get("ΓΕΝΕΣΙΣ")  # Returns "Gen"

Notes:
- Brenton uses Greek book names
- Some books appear in multiple versions in Rahlfs (e.g., JoshA/JoshB, DanOG/DanTh)
- Some books exist in one edition but not others
- The second occurrence of ΕΣΔΡΑΣ in Brenton refers to 1 Esdras (apocryphal)
"""

# Mapping from Brenton Greek book names to Swete book codes
BRENTON_TO_SWETE = {
    # Pentateuch
    "ΓΕΝΕΣΙΣ": "Gen",
    "ΕΞΟΔΟΣ": "Exo",
    "ΛΕΥΙΤΙΚΟΝ": "Lev",
    "ΑΡΙΘΜΟΙ": "Num",
    "ΔΕΥΤΕΡΟΝΟΜΙΟΝ": "Deu",
    
    # Historical Books
    "ΙΗΣΟΥΣ ΝΑΥΗ": "Jos",
    "ΚΡΙΤΑΙ": "Jdg",
    "ΡΟΥΘ": "Rut",
    "ΒΑΣΙΛΕΙΩΝ Α": "1Sa",  # 1 Samuel
    "ΒΑΣΙΛΕΙΩΝ Β": "2Sa",  # 2 Samuel
    "ΒΑΣΙΛΕΙΩΝ Γ": "1Ki",  # 1 Kings
    "ΒΑΣΙΛΕΙΩΝ Δ": "2Ki",  # 2 Kings
    "ΠΑΡΑΛΕΙΠΟΜΕΝΩΝ Α": "1Ch",  # 1 Chronicles
    "ΠΑΡΑΛΕΙΠΟΜΕΝΩΝ Β": "2Ch",  # 2 Chronicles
    
    # Ezra-Nehemiah (now separated in Brenton)
    "ΕΣΔΡΑΣ": "Ezr",  # Canonical Ezra
    "ΝΕΕΜΙΑΣ": "Neh",  # Nehemiah
    "ΕΣΔΡΑΣ Α": "1Es",  # 1 Esdras (apocryphal, appears after Malachi)
    
    "ΕΣΘΗΡ": "Est",
    
    # Wisdom Books
    "ΙΩΒ": "Job",
    "ΨΑΛΜΟΙ": "Psa",
    "ΠΑΡΟΙΜΙΑΙ ΣΑΛΩΜΩΝΤΟΣ": "Pro",
    "ΕΚΚΛΗΣΙΑΣΤΗΣ": "Ecc",
    "ΑΣΜΑ": "Sol",  # Song of Solomon
    
    # Major Prophets
    "ΗΣΑΙΑΣ": "Isa",
    "ΙΕΡΕΜΙΑΣ": "Jer",
    "ΘΡΗΝΟΙ ΙΕΡΕΜΙΟΥ": "Lam",
    "ΙΕΖΕΚΙΗΛ": "Eze",
    "ΔΑΝΙΗΛ": "Dan",
    
    # Minor Prophets (The Twelve)
    "ΩΣΗΕ": "Hos",
    "ΙΩΗΛ": "Joe",
    "ΑΜΩΣ": "Amo",
    "ΟΒΔΕΙΟΥ": "Oba",
    "ΙΩΝΑΣ": "Jon",
    "ΜΙΧΑΙΑΣ": "Mic",
    "ΝΑΟΥΜ": "Nah",
    "ΑΜΒΑΚΟΥΜ": "Hab",
    "ΣΟΦΟΝΙΑΣ": "Zep",
    "ΑΓΓΑΙΟΣ": "Hag",
    "ΖΑΧΑΡΙΑΣ": "Zec",
    "ΜΑΛΑΧΙΑΣ": "Mal",
    
    # Apocryphal/Deuterocanonical Books
    # Note: Second ΕΣΔΡΑΣ occurrence maps to 1 Esdras
    # "ΕΣΔΡΑΣ" (second): "1Es",  # 1 Esdras - needs context to distinguish
    "ΤΩΒΙΤ": "Tob",
    "ΙΟΥΔΙΘ": "Jdt",
    "ΣΟΦΙΑ ΣΑΛΩΜΩΝ": "Wis",
    "ΣΟΦΙΑ ΣΕΙΡΑΧ": "Sir",  # Sirach/Ecclesiasticus
    "ΒΑΡΟΥΧ": "Bar",
    "ΕΠΙΣΤΟΛΗ ΙΕΡΕΜΙΟΥ": "Epj",  # Letter of Jeremiah
    "ΣΩΣΑΝΝΑ": "Sus",  # Susanna
    "ΒΗΛ ΚΑΙ ΔΡΑΚΩΝ": "Bel",  # Bel and the Dragon
    "ΜΑΚΚΑΒΑΙΩΝ Α": "1Ma",  # 1 Maccabees
    "ΜΑΚΚΑΒΑΙΩΝ Β": "2Ma",  # 2 Maccabees
    "ΜΑΚΚΑΒΑΙΩΝ Γ": "3Ma",  # 3 Maccabees
    "ΜΑΚΚΑΒΑΙΩΝ Δ": "4Ma",  # 4 Maccabees
    "ΠΡΟΣΕΥΧΗ ΜΑΝΑΣΣΗ ΥΙΟΥ ΕΖΕΚΙΟΥ": "Ode",  # Prayer of Manasseh (often in Odes)
}

# Mapping from Brenton Greek book names to Rahlfs book codes
BRENTON_TO_RAHLFS = {
    # Pentateuch
    "ΓΕΝΕΣΙΣ": "Gen",
    "ΕΞΟΔΟΣ": "Exod",
    "ΛΕΥΙΤΙΚΟΝ": "Lev",
    "ΑΡΙΘΜΟΙ": "Num",
    "ΔΕΥΤΕΡΟΝΟΜΙΟΝ": "Deut",
    
    # Historical Books
    # Note: Rahlfs has JoshA and JoshB (two versions of Joshua)
    # Brenton appears to follow one text tradition, likely closer to JoshB
    "ΙΗΣΟΥΣ ΝΑΥΗ": "JoshB",  # Joshua - using B text (more common in LXX editions)
    
    # Note: Rahlfs has JudgA and JudgB (two versions of Judges)
    # Brenton appears to follow one text tradition, likely closer to JudgB
    "ΚΡΙΤΑΙ": "JudgB",  # Judges - using B text (more common in LXX editions)
    
    "ΡΟΥΘ": "Ruth",
    "ΒΑΣΙΛΕΙΩΝ Α": "1Sam",  # 1 Samuel (called 1 Kingdoms in LXX)
    "ΒΑΣΙΛΕΙΩΝ Β": "2Sam",  # 2 Samuel (called 2 Kingdoms in LXX)
    "ΒΑΣΙΛΕΙΩΝ Γ": "1Kgs",  # 1 Kings (called 3 Kingdoms in LXX)
    "ΒΑΣΙΛΕΙΩΝ Δ": "2Kgs",  # 2 Kings (called 4 Kingdoms in LXX)
    "ΠΑΡΑΛΕΙΠΟΜΕΝΩΝ Α": "1Chr",  # 1 Chronicles
    "ΠΑΡΑΛΕΙΠΟΜΕΝΩΝ Β": "2Chr",  # 2 Chronicles
    
    # Ezra-Nehemiah (now separated in Brenton)
    # Note: Rahlfs has 2Esdr which combines Ezra and Nehemiah
    "ΕΣΔΡΑΣ": "2Esdr",  # Canonical Ezra (Rahlfs combines Ezra-Nehemiah as 2Esdr)
    "ΝΕΕΜΙΑΣ": "2Esdr",  # Nehemiah (also part of 2Esdr in Rahlfs)
    "ΕΣΔΡΑΣ Α": "1Esdr",  # 1 Esdras (apocryphal, appears after Malachi)
    
    "ΕΣΘΗΡ": "Esth",
    
    # Wisdom Books
    "ΙΩΒ": "Job",
    "ΨΑΛΜΟΙ": "Ps",
    "ΠΑΡΟΙΜΙΑΙ ΣΑΛΩΜΩΝΤΟΣ": "Prov",
    "ΕΚΚΛΗΣΙΑΣΤΗΣ": "Eccl",
    "ΑΣΜΑ": "Song",  # Song of Songs/Song of Solomon
    
    # Major Prophets
    "ΗΣΑΙΑΣ": "Isa",
    "ΙΕΡΕΜΙΑΣ": "Jer",
    "ΘΡΗΝΟΙ ΙΕΡΕΜΙΟΥ": "Lam",
    "ΙΕΖΕΚΙΗΛ": "Ezek",
    
    # Note: Rahlfs has DanOG (Old Greek) and DanTh (Theodotion) versions
    # Brenton likely follows Theodotion (more common in LXX editions)
    "ΔΑΝΙΗΛ": "DanTh",  # Daniel - Theodotion version
    
    # Minor Prophets (The Twelve)
    "ΩΣΗΕ": "Hos",
    "ΙΩΗΛ": "Joel",
    "ΑΜΩΣ": "Amos",
    "ΟΒΔΕΙΟΥ": "Obad",
    "ΙΩΝΑΣ": "Jonah",
    "ΜΙΧΑΙΑΣ": "Mic",
    "ΝΑΟΥΜ": "Nah",
    "ΑΜΒΑΚΟΥΜ": "Hab",
    "ΣΟΦΟΝΙΑΣ": "Zeph",
    "ΑΓΓΑΙΟΣ": "Hag",
    "ΖΑΧΑΡΙΑΣ": "Zech",
    "ΜΑΛΑΧΙΑΣ": "Mal",
    
    # Apocryphal/Deuterocanonical Books
    # Note: Second ΕΣΔΡΑΣ occurrence maps to 1 Esdras
    # "ΕΣΔΡΑΣ" (second): "1Esdr",  # 1 Esdras - needs context to distinguish
    
    # Note: Rahlfs has TobBA and TobS (two versions of Tobit)
    # Brenton likely follows the Sinaiticus version
    "ΤΩΒΙΤ": "TobS",  # Tobit - Sinaiticus version
    
    "ΙΟΥΔΙΘ": "Jdt",
    "ΣΟΦΙΑ ΣΑΛΩΜΩΝ": "Wis",
    "ΣΟΦΙΑ ΣΕΙΡΑΧ": "Sir",  # Sirach/Ecclesiasticus
    "ΒΑΡΟΥΧ": "Bar",
    "ΕΠΙΣΤΟΛΗ ΙΕΡΕΜΙΟΥ": "EpJer",  # Letter of Jeremiah
    
    # Note: Rahlfs has SusOG (Old Greek) and SusTh (Theodotion) versions
    # Brenton likely follows Theodotion
    "ΣΩΣΑΝΝΑ": "SusTh",  # Susanna - Theodotion version
    
    # Note: Rahlfs has BelOG (Old Greek) and BelTh (Theodotion) versions
    # Brenton likely follows Theodotion
    "ΒΗΛ ΚΑΙ ΔΡΑΚΩΝ": "BelTh",  # Bel and the Dragon - Theodotion version
    
    "ΜΑΚΚΑΒΑΙΩΝ Α": "1Macc",  # 1 Maccabees
    "ΜΑΚΚΑΒΑΙΩΝ Β": "2Macc",  # 2 Maccabees
    "ΜΑΚΚΑΒΑΙΩΝ Γ": "3Macc",  # 3 Maccabees
    "ΜΑΚΚΑΒΑΙΩΝ Δ": "4Macc",  # 4 Maccabees
    "ΠΡΟΣΕΥΧΗ ΜΑΝΑΣΣΗ ΥΙΟΥ ΕΖΕΚΙΟΥ": "Odes",  # Prayer of Manasseh (in Odes)
}

# Note: ΕΣΔΡΑΣ and ΕΣΔΡΑΣ Α are now distinct in Brenton
# - ΕΣΔΡΑΣ = canonical Ezra (appears after 2 Chronicles)
# - ΝΕΕΜΙΑΣ = Nehemiah (appears after Ezra)
# - ΕΣΔΡΑΣ Α = 1 Esdras apocryphal (appears after Malachi)


# Reverse mappings (for convenience)
SWETE_TO_BRENTON = {v: k for k, v in BRENTON_TO_SWETE.items()}
RAHLFS_TO_BRENTON = {v: k for k, v in BRENTON_TO_RAHLFS.items()}


# Utility functions for verse reference conversion

def convert_brenton_chapter_to_rahlfs(brenton_book: str, brenton_chapter: int) -> tuple[str, int]:
    """
    Convert a Brenton book and chapter to Rahlfs book and chapter.
    
    Handles the special case where Ezra and Nehemiah are separate in Brenton
    but combined as 2Esdr in Rahlfs:
    - ΕΣΔΡΑΣ chapters 1-10 → 2Esdr chapters 1-10
    - ΝΕΕΜΙΑΣ chapters 1-13 → 2Esdr chapters 11-23
    
    Args:
        brenton_book: The Greek book name from Brenton (e.g., "ΕΣΔΡΑΣ", "ΝΕΕΜΙΑΣ")
        brenton_chapter: The chapter number in Brenton
    
    Returns:
        A tuple of (rahlfs_book_code, rahlfs_chapter)
        
    Examples:
        >>> convert_brenton_chapter_to_rahlfs("ΕΣΔΡΑΣ", 8)
        ('2Esdr', 8)
        >>> convert_brenton_chapter_to_rahlfs("ΝΕΕΜΙΑΣ", 1)
        ('2Esdr', 11)
        >>> convert_brenton_chapter_to_rahlfs("ΓΕΝΕΣΙΣ", 14)
        ('Gen', 14)
    """
    if brenton_book == "ΝΕΕΜΙΑΣ":
        # Nehemiah chapters 1-13 map to 2Esdr chapters 11-23
        return ("2Esdr", brenton_chapter + 10)
    
    # For all other books (including ΕΣΔΡΑΣ), use the standard mapping
    rahlfs_book = BRENTON_TO_RAHLFS.get(brenton_book)
    if rahlfs_book is None:
        raise ValueError(f"Unknown Brenton book: {brenton_book}")
    
    return (rahlfs_book, brenton_chapter)


def convert_brenton_chapter_to_swete(brenton_book: str, brenton_chapter: int) -> tuple[str, int]:
    """
    Convert a Brenton book and chapter to Swete book and chapter.
    
    Swete keeps Ezra (Ezr) and Nehemiah (Neh) separate, so this is mostly
    a straightforward lookup, but provided for consistency with Rahlfs conversion.
    
    Args:
        brenton_book: The Greek book name from Brenton (e.g., "ΕΣΔΡΑΣ", "ΝΕΕΜΙΑΣ")
        brenton_chapter: The chapter number in Brenton
    
    Returns:
        A tuple of (swete_book_code, swete_chapter)
        
    Examples:
        >>> convert_brenton_chapter_to_swete("ΕΣΔΡΑΣ", 8)
        ('Ezr', 8)
        >>> convert_brenton_chapter_to_swete("ΝΕΕΜΙΑΣ", 1)
        ('Neh', 1)
        >>> convert_brenton_chapter_to_swete("ΓΕΝΕΣΙΣ", 14)
        ('Gen', 14)
    """
    swete_book = BRENTON_TO_SWETE.get(brenton_book)
    if swete_book is None:
        raise ValueError(f"Unknown Brenton book: {brenton_book}")
    
    return (swete_book, brenton_chapter)


def convert_brenton_reference_to_rahlfs(brenton_book: str, chapter: int, verse: int) -> str:
    """
    Convert a full Brenton verse reference to Rahlfs format.
    
    Args:
        brenton_book: The Greek book name from Brenton (e.g., "ΓΕΝΕΣΙΣ", "ΕΣΔΡΑΣ", "ΝΕΕΜΙΑΣ")
        chapter: The chapter number
        verse: The verse number
    
    Returns:
        A string in Rahlfs format: "Book.Chapter.Verse" (e.g., "Gen.14.7", "2Esdr.11.2")
        
    Examples:
        >>> convert_brenton_reference_to_rahlfs("ΓΕΝΕΣΙΣ", 14, 7)
        'Gen.14.7'
        >>> convert_brenton_reference_to_rahlfs("ΕΣΔΡΑΣ", 8, 35)
        '2Esdr.8.35'
        >>> convert_brenton_reference_to_rahlfs("ΝΕΕΜΙΑΣ", 1, 2)
        '2Esdr.11.2'
    """
    rahlfs_book, rahlfs_chapter = convert_brenton_chapter_to_rahlfs(brenton_book, chapter)
    return f"{rahlfs_book}.{rahlfs_chapter}.{verse}"


def convert_brenton_reference_to_swete(brenton_book: str, chapter: int, verse: int) -> str:
    """
    Convert a full Brenton verse reference to Swete format.
    
    Args:
        brenton_book: The Greek book name from Brenton (e.g., "ΓΕΝΕΣΙΣ", "ΕΣΔΡΑΣ", "ΝΕΕΜΙΑΣ")
        chapter: The chapter number
        verse: The verse number
    
    Returns:
        A string in Swete format: "Book.Chapter:Verse" (e.g., "Gen.14:7", "Neh.1:2")
        
    Examples:
        >>> convert_brenton_reference_to_swete("ΓΕΝΕΣΙΣ", 14, 7)
        'Gen.14:7'
        >>> convert_brenton_reference_to_swete("ΕΣΔΡΑΣ", 8, 35)
        'Ezr.8:35'
        >>> convert_brenton_reference_to_swete("ΝΕΕΜΙΑΣ", 1, 2)
        'Neh.1:2'
    """
    swete_book, swete_chapter = convert_brenton_chapter_to_swete(brenton_book, chapter)
    return f"{swete_book}.{swete_chapter}:{verse}"


def parse_brenton_reference(reference: str) -> tuple[str, int, int]:
    """
    Parse a Brenton verse reference string into its components.
    
    Accepts formats like:
    - "ΓΕΝΕΣΙΣ 14:7"
    - "ΕΣΔΡΑΣ 8:35"
    - "ΝΕΕΜΙΑΣ 1:2"
    
    Args:
        reference: A verse reference string in Brenton format
    
    Returns:
        A tuple of (book_name, chapter, verse)
        
    Examples:
        >>> parse_brenton_reference("ΓΕΝΕΣΙΣ 14:7")
        ('ΓΕΝΕΣΙΣ', 14, 7)
        >>> parse_brenton_reference("ΕΣΔΡΑΣ 8:35")
        ('ΕΣΔΡΑΣ', 8, 35)
        >>> parse_brenton_reference("ΝΕΕΜΙΑΣ 1:2")
        ('ΝΕΕΜΙΑΣ', 1, 2)
    """
    # Split on space to separate book from chapter:verse
    parts = reference.strip().split(' ')
    if len(parts) != 2:
        raise ValueError(f"Invalid reference format: {reference}. Expected 'BOOK C:V'")
    
    book_name = parts[0]
    
    # Split chapter:verse
    cv_parts = parts[1].split(':')
    if len(cv_parts) != 2:
        raise ValueError(f"Invalid chapter:verse format: {parts[1]}. Expected 'C:V'")
    
    try:
        chapter = int(cv_parts[0])
        verse = int(cv_parts[1])
    except ValueError as e:
        raise ValueError(f"Chapter and verse must be integers: {parts[1]}") from e
    
    return (book_name, chapter, verse)

# Note: The reverse mappings will have duplicates for books with multiple versions
# For example, both "JoshA" and "JoshB" would need special handling


# Additional notes for uncertain mappings:
"""
UNCERTAIN MAPPINGS (may need verification):

1. Joshua and Judges:
   - Rahlfs has A and B versions (JoshA/JoshB, JudgA/JudgB)
   - Brenton likely follows the B text (more common), but this should be verified
   - Swete appears to have only one version each

2. Daniel additions:
   - Rahlfs has both Old Greek (OG) and Theodotion (Th) versions
   - Brenton likely uses Theodotion (more common in printed LXX)
   - Should be verified by comparing verse numbers

3. Tobit:
   - Rahlfs has TobBA (short version) and TobS (Sinaiticus, longer version)
   - Brenton should be checked to determine which version it follows

4. Prayer of Manasseh:
   - Mapped to Odes in both editions
   - This prayer is often included in the Odes/Canticles section
   - May need verification of exact location in versification files

5. Ezra-Nehemiah in Rahlfs:
   - Rahlfs combines Ezra and Nehemiah into 2Esdr
   - Brenton now has them separated as ΕΣΔΡΑΣ and ΝΕΕΜΙΑΣ
   - Both map to 2Esdr in Rahlfs (you'll need to use verse numbers to distinguish)

6. Books present in Swete but not clearly in Rahlfs:
   - Some codes in Swete (1En, Bet, Dat, Sip, Tbs, Sut) don't have clear Rahlfs equivalents
   - These may be alternate versions or additional texts
"""
