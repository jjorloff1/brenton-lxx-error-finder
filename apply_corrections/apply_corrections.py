#!/usr/bin/env python3
"""
Apply corrections from word_corrections.tsv to LaTeX source files.

This script reads corrections from a TSV file and applies them to LaTeX source
files containing Greek text of the Septuagint. It produces corrected output files
and a detailed log of all changes made.
"""

import os
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class Correction:
    """Represents a single correction to apply."""
    verse_ref: str  # e.g., "ΓΕΝΕΣΙΣ 14:22" or "ALL"
    incorrect: str  # The text to find and replace
    correct: str    # The replacement text
    notes: str      # Optional notes about the correction
    line_num: int   # Line number in the TSV file (for reference)

    @property
    def book_name(self) -> Optional[str]:
        """Extract the book name from the verse reference."""
        if self.verse_ref == "ALL":
            return None
        # The verse reference is "BOOK_NAME chapter:verse"
        # Book name is everything before the last space-separated chapter:verse
        parts = self.verse_ref.rsplit(' ', 1)
        if len(parts) == 2 and ':' in parts[1]:
            return parts[0]
        # Handle cases where there might not be a proper chapter:verse
        return self.verse_ref

    @property
    def chapter_verse(self) -> Optional[str]:
        """Extract the chapter:verse from the verse reference."""
        if self.verse_ref == "ALL":
            return None
        parts = self.verse_ref.rsplit(' ', 1)
        if len(parts) == 2 and ':' in parts[1]:
            return parts[1]
        return None


@dataclass
class LogEntry:
    """Represents a log entry for a correction."""
    filename: str
    line_num: int
    correction: Correction
    found_at_expected: bool  # Whether it was found at the expected verse
    actual_location: str     # Description of where it was actually found
    success: bool


def build_book_mapping(source_dir: Path) -> dict[str, str]:
    """
    Build a mapping from Greek book names to filenames.

    Reads each file and extracts the book name from the \\MT tag.
    """
    mapping = {}

    for filename in os.listdir(source_dir):
        if not filename.endswith('_src.tex'):
            continue

        filepath = source_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the \MT tag - format is "{\MT BOOK_NAME" on its own line
        match = re.search(r'\{\\MT\s+(.+?)(?:\n|$)', content)
        if match:
            book_name = match.group(1).strip()
            # Strip ordinal suffix from minor prophets (e.g., "ΩΣΗΕ. Αʹ" -> "ΩΣΗΕ")
            # The suffix is ". " followed by a Greek numeral with keraia (ʹ)
            book_name = re.sub(r'\.\s+[ΑΒΓΔΕϛΖΗΘΙ]+ʹ$', '', book_name)
            mapping[book_name] = filename

    return mapping


def parse_corrections(tsv_path: Path) -> tuple[list[Correction], list[Correction], list[Correction]]:
    """
    Parse the corrections TSV file.

    Returns:
        - specific_corrections: corrections with specific verse references
        - all_corrections: corrections with "ALL" (excluding last 7)
        - diacritical_corrections: last 7 "ALL" corrections (diacritical fixes)
    """
    all_corrections_list = []
    specific_corrections = []

    with open(tsv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        line = line.rstrip('\n\r')

        # Skip blank lines
        if not line.strip():
            continue

        # Skip comment lines
        if line.strip().startswith('#'):
            continue

        # Split by tab
        parts = line.split('\t')
        if len(parts) < 3:
            print(f"Warning: Line {i} has fewer than 3 columns, skipping: {line[:50]}...")
            continue

        verse_ref = parts[0].strip()
        incorrect = parts[1]  # Don't strip - preserve internal spacing
        correct = parts[2]    # Don't strip - preserve internal spacing
        notes = parts[3] if len(parts) > 3 else ""

        # Skip if incorrect and correct are the same
        if incorrect == correct:
            print(f"Warning: Line {i} has identical incorrect and correct values, skipping")
            continue

        correction = Correction(
            verse_ref=verse_ref,
            incorrect=incorrect,
            correct=correct,
            notes=notes,
            line_num=i
        )

        if verse_ref == "ALL":
            all_corrections_list.append(correction)
        else:
            specific_corrections.append(correction)

    # Separate the last 7 ALL corrections (diacritical fixes)
    # These are lines 622-628 in the TSV (the ʼ to breathing mark conversions)
    if len(all_corrections_list) >= 7:
        diacritical_corrections = all_corrections_list[-7:]
        all_corrections = all_corrections_list[:-7]
    else:
        diacritical_corrections = []
        all_corrections = all_corrections_list

    # Sort corrections by length of incorrect string (longest first)
    # This prevents shorter substrings from corrupting longer words
    # For example, "ἐγ" -> "ἐν" must not run before "ἐγαπημένον" -> "ἠγαπημένον"
    specific_corrections.sort(key=lambda c: len(c.incorrect), reverse=True)
    all_corrections.sort(key=lambda c: len(c.incorrect), reverse=True)
    # Note: diacritical_corrections stay in original order (they're single chars)

    return specific_corrections, all_corrections, diacritical_corrections


def is_greek_letter(char: str) -> bool:
    """
    Check if a character is a Greek letter (including accented forms).

    This helps identify word boundaries in Greek text.
    Note: Modifier letter apostrophe (ʼ) is NOT a letter - it's punctuation.
    """
    if not char:
        return False
    code = ord(char)
    # Greek and Coptic block: U+0370 to U+03FF
    # Greek Extended block: U+1F00 to U+1FFF
    return (0x0370 <= code <= 0x03FF or  # Greek and Coptic
            0x1F00 <= code <= 0x1FFF)    # Greek Extended


def is_word_boundary_before(content: str, pos: int) -> bool:
    """
    Check if position is at the start of a word (preceded by non-letter or start of string).
    """
    if pos == 0:
        return True
    prev_char = content[pos - 1]
    return not is_greek_letter(prev_char)


def is_word_boundary_after(content: str, pos: int, match_len: int) -> bool:
    """
    Check if the position after the match is at a word boundary.
    """
    end_pos = pos + match_len
    if end_pos >= len(content):
        return True
    next_char = content[end_pos]
    return not is_greek_letter(next_char)


def find_verse_at_position(content: str, position: int) -> str:
    """
    Find the verse reference at a given position in the content.

    Returns a string like "Chapter 5, Verse 12" or "Unknown".
    """
    # Find the most recent chapter marker before this position
    chapter_pattern = r'\\(?:Chap(?:One)?|PsalmChap|OneChap)\{?(\d*)\}?'
    chapter = "?"
    for match in re.finditer(chapter_pattern, content[:position]):
        chapter = match.group(1) if match.group(1) else "1"

    # Handle \OneChap (single chapter books)
    if '\\OneChap' in content[:position]:
        chapter = "1"

    # Find the most recent verse marker before this position
    verse_pattern = r'\\(?:VS|VerseOne)\{(\d+[a-z]?)\}'
    verse = "?"
    for match in re.finditer(verse_pattern, content[:position]):
        verse = match.group(1)

    return f"Chapter {chapter}, Verse {verse}"


def apply_corrections_to_content(
    content: str,
    corrections: list[Correction],
    filename: str,
    book_name: str,
    log_entries: list[LogEntry],
    check_verse_ref: bool = True
) -> str:
    """
    Apply a list of corrections to the content.

    Args:
        content: The file content to modify
        corrections: List of corrections to apply
        filename: The filename (for logging)
        book_name: The Greek book name (for matching)
        log_entries: List to append log entries to
        check_verse_ref: Whether to check if correction is at expected verse

    Returns:
        Modified content
    """
    for correction in corrections:
        # For specific corrections, check if this is the right book
        if correction.book_name is not None and correction.book_name != book_name:
            continue

        # Find all occurrences of the incorrect text at word boundaries
        # We require the match to start at a word boundary (not in the middle of a word)
        # For short corrections (<=3 chars), we also require it to end at a word boundary
        # Exception: if the string itself starts/ends with a space, that IS the boundary
        positions = []
        start = 0
        match_len = len(correction.incorrect)

        # Check if the correction string itself provides boundaries
        has_leading_space = correction.incorrect.startswith(' ')
        has_trailing_space = correction.incorrect.endswith(' ')

        # Diacritical corrections (like ʼΙ → Ἰ) start with the apostrophe and are
        # always at word starts - they shouldn't require an end boundary
        is_diacritical_fix = correction.incorrect.startswith('ʼ')

        while True:
            pos = content.find(correction.incorrect, start)
            if pos == -1:
                break

            # Check word boundaries (unless the string itself provides them)
            starts_at_boundary = has_leading_space or is_word_boundary_before(content, pos)
            ends_at_boundary = has_trailing_space or is_word_boundary_after(content, pos, match_len)

            # Require both start and end boundaries to avoid partial word matches
            # Exception: diacritical fixes (ʼX → proper breathing mark) only need start boundary
            # because they're always at word starts followed by more letters
            if starts_at_boundary:
                if is_diacritical_fix or ends_at_boundary:
                    positions.append(pos)

            start = pos + 1

        if not positions:
            # Correction not found in this file
            if correction.book_name == book_name:
                # This correction was expected in this file but not found
                log_entries.append(LogEntry(
                    filename=filename,
                    line_num=0,
                    correction=correction,
                    found_at_expected=False,
                    actual_location="NOT FOUND",
                    success=False
                ))
            continue

        # Handle verse-specific corrections differently from ALL/book-wide
        if check_verse_ref and correction.chapter_verse:
            # Filter to only positions at the expected verse
            expected_parts = correction.chapter_verse.split(':')
            if len(expected_parts) == 2:
                expected_ch, expected_vs = expected_parts
                # Remove any letter suffix from verse for comparison
                expected_vs_num = re.sub(r'[a-z]$', '', expected_vs)

                positions_at_verse = []
                positions_elsewhere = []

                for pos in positions:
                    actual_verse = find_verse_at_position(content, pos)
                    if (f"Chapter {expected_ch}" in actual_verse and
                        f"Verse {expected_vs_num}" in actual_verse):
                        positions_at_verse.append((pos, actual_verse))
                    else:
                        positions_elsewhere.append((pos, actual_verse))

                if not positions_at_verse:
                    # Not found at expected verse
                    elsewhere_info = ""
                    if positions_elsewhere:
                        elsewhere_info = f" (found {len(positions_elsewhere)} elsewhere in book)"
                    log_entries.append(LogEntry(
                        filename=filename,
                        line_num=0,
                        correction=correction,
                        found_at_expected=False,
                        actual_location=f"NOT FOUND at {correction.verse_ref}{elsewhere_info}",
                        success=False
                    ))
                    continue

                # Log and apply corrections at the expected verse
                warning_suffix = ""
                if len(positions_at_verse) > 1:
                    warning_suffix = f" [WARNING: {len(positions_at_verse)} matches in verse]"

                for pos, actual_verse in positions_at_verse:
                    log_entries.append(LogEntry(
                        filename=filename,
                        line_num=content[:pos].count('\n') + 1,
                        correction=correction,
                        found_at_expected=True,
                        actual_location=f"{actual_verse}{warning_suffix}",
                        success=True
                    ))

                # Only replace at verse-specific positions
                for pos, _ in reversed(positions_at_verse):
                    content = content[:pos] + correction.correct + content[pos + len(correction.incorrect):]
        else:
            # ALL corrections or book-wide: apply everywhere (existing behavior)
            for pos in reversed(positions):  # Reverse to maintain positions
                # Calculate line number in the file
                line_num = content[:pos].count('\n') + 1

                # Find what verse this is in
                actual_verse = find_verse_at_position(content, pos)

                log_entries.append(LogEntry(
                    filename=filename,
                    line_num=line_num,
                    correction=correction,
                    found_at_expected=True,  # ALL corrections are always "expected"
                    actual_location=actual_verse,
                    success=True
                ))

                # Apply the replacement
                content = content[:pos] + correction.correct + content[pos + len(correction.incorrect):]

    return content


def main():
    # Paths
    base_dir = Path(__file__).parent
    source_dir = base_dir / "grcbrent_xetex_original"
    output_dir = base_dir / "grcbrent_xetex_corrected"
    tsv_path = base_dir.parent / "word_corrections.tsv"  # TSV is in parent directory (shared)
    log_path = output_dir / "correction_log.txt"  # Log goes in output directory

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    print("Building book name to filename mapping...")
    book_mapping = build_book_mapping(source_dir)
    print(f"Found {len(book_mapping)} books")

    # Create reverse mapping for lookup
    filename_to_book = {v: k for k, v in book_mapping.items()}

    print("\nParsing corrections TSV...")
    specific_corrections, all_corrections, diacritical_corrections = parse_corrections(tsv_path)
    print(f"Found {len(specific_corrections)} specific corrections")
    print(f"Found {len(all_corrections)} ALL corrections")
    print(f"Found {len(diacritical_corrections)} diacritical corrections (to apply last)")

    # Group specific corrections by book
    corrections_by_book: dict[str, list[Correction]] = {}
    for correction in specific_corrections:
        book = correction.book_name
        if book:
            if book not in corrections_by_book:
                corrections_by_book[book] = []
            corrections_by_book[book].append(correction)

    # Process each file
    log_entries: list[LogEntry] = []
    files_processed = 0

    print("\nProcessing files...")
    for filename in sorted(os.listdir(source_dir)):
        if not filename.endswith('_src.tex'):
            continue

        filepath = source_dir / filename
        book_name = filename_to_book.get(filename, "")

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Apply specific corrections for this book
        book_corrections = corrections_by_book.get(book_name, [])
        if book_corrections:
            content = apply_corrections_to_content(
                content, book_corrections, filename, book_name, log_entries,
                check_verse_ref=True
            )

        # 2. Apply ALL corrections (non-diacritical)
        content = apply_corrections_to_content(
            content, all_corrections, filename, book_name, log_entries,
            check_verse_ref=False
        )

        # 3. Apply diacritical ALL corrections (last 7)
        content = apply_corrections_to_content(
            content, diacritical_corrections, filename, book_name, log_entries,
            check_verse_ref=False
        )

        # Write output file
        output_path = output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        files_processed += 1

        # Report changes for this file
        file_changes = sum(1 for e in log_entries if e.filename == filename and e.success)
        if file_changes > 0:
            print(f"  {filename}: {file_changes} corrections applied")

    print(f"\nProcessed {files_processed} files")

    # Generate log file
    print(f"\nWriting log to {log_path}...")

    successful_corrections = [e for e in log_entries if e.success]
    failed_corrections = [e for e in log_entries if not e.success]
    unexpected_locations = [e for e in successful_corrections if not e.found_at_expected]

    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("CORRECTION LOG\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Total corrections applied: {len(successful_corrections)}\n")
        f.write(f"Corrections not found: {len(failed_corrections)}\n")
        f.write(f"Corrections at unexpected locations: {len(unexpected_locations)}\n\n")

        # Successful corrections
        f.write("-" * 80 + "\n")
        f.write("SUCCESSFUL CORRECTIONS\n")
        f.write("-" * 80 + "\n\n")

        for entry in successful_corrections:
            location_note = ""
            if not entry.found_at_expected and entry.correction.verse_ref != "ALL":
                location_note = f" [UNEXPECTED: expected {entry.correction.verse_ref}, found at {entry.actual_location}]"

            f.write(f"File: {entry.filename}, Line {entry.line_num}\n")
            f.write(f"  TSV Line: {entry.correction.line_num}\n")
            f.write(f"  Reference: {entry.correction.verse_ref}\n")
            f.write(f"  Changed: '{entry.correction.incorrect}' -> '{entry.correction.correct}'\n")
            f.write(f"  Location: {entry.actual_location}{location_note}\n")
            if entry.correction.notes:
                f.write(f"  Notes: {entry.correction.notes}\n")
            f.write("\n")

        # Failed corrections
        if failed_corrections:
            f.write("-" * 80 + "\n")
            f.write("CORRECTIONS NOT FOUND\n")
            f.write("-" * 80 + "\n\n")

            for entry in failed_corrections:
                f.write(f"TSV Line {entry.correction.line_num}: {entry.correction.verse_ref}\n")
                f.write(f"  Expected in: {entry.filename}\n")
                f.write(f"  Looking for: '{entry.correction.incorrect}'\n")
                f.write(f"  Correction: '{entry.correction.correct}'\n")
                if entry.correction.notes:
                    f.write(f"  Notes: {entry.correction.notes}\n")
                f.write("\n")

        # Summary by file
        f.write("-" * 80 + "\n")
        f.write("SUMMARY BY FILE\n")
        f.write("-" * 80 + "\n\n")

        files_with_changes = {}
        for entry in successful_corrections:
            if entry.filename not in files_with_changes:
                files_with_changes[entry.filename] = 0
            files_with_changes[entry.filename] += 1

        for filename, count in sorted(files_with_changes.items()):
            f.write(f"{filename}: {count} corrections\n")

    print(f"\nDone! Corrected files written to {output_dir}")
    print(f"Log written to {log_path}")
    print(f"\nSummary:")
    print(f"  - {len(successful_corrections)} corrections applied successfully")
    print(f"  - {len(failed_corrections)} corrections not found")
    print(f"  - {len(unexpected_locations)} found at unexpected locations")


if __name__ == "__main__":
    main()
