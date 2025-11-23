#!/usr/bin/env python3
"""
Compare two editions of an LXX book (Brenton .tex and Swete .txt).

- Parses Brenton LaTeX source (e.g. GEN_src.tex) into verses keyed as "book.chapter.verse".
- Parses Swete text source (e.g. 01.Genesis.txt) into the same key format.
- Compares verses and writes a tab-delimited output file.

Default comparison mode: "simple" (no LLM).
Optional comparison mode: "gemini" using LangChain + Gemini (see notes below).

Example:

    python compare_lxx_editions.py \
        --brenton /mnt/data/GEN_src.tex \
        --swete /mnt/data/01.Genesis.txt \
        --mode simple
"""

import argparse
import difflib
import os
import re
from pathlib import Path
from typing import Dict, Tuple, List, Iterable


# ---------- Parsing helpers ----------

def strip_tex(text: str) -> str:
    """
    Strip basic TeX commands/macros and normalize whitespace.
    This is deliberately simple; adjust if you need to keep more structure.
    """
    # Remove commands like \PP, \par, \MT{...}, \FT{...}, etc.
    text = re.sub(r"\\[A-Za-z]+(\{[^}]*\})*", "", text)
    # Remove remaining braces
    text = text.replace("{", "").replace("}", "")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_brenton_tex(path: Path, book_num: int) -> Dict[str, str]:
    """
    Parse a Brenton LaTeX file into a dict mapping "book.chapter.verse" -> verse text.

    Assumes chapters are marked with \Chap*{<number>}
    and verses with \VerseOne{<v>} (first verse) or \VS{<v>} (subsequent verses).
    """
    text = path.read_text(encoding="utf-8")

    # Find all chapter markers with their positions
    chap_matches = list(re.finditer(r"\\Chap\w*?\{(\d+)\}", text))
    verses: Dict[str, str] = {}

    for i, m in enumerate(chap_matches):
        chap_num = int(m.group(1))
        start = m.end()
        end = chap_matches[i + 1].start() if i + 1 < len(chap_matches) else len(text)
        chap_text = text[start:end]

        # Find verse markers inside this chapter chunk
        verse_matches = list(
            re.finditer(r"(\\VerseOne\{(\d+)\}|\\VS\{(\d+)\})", chap_text)
        )

        for j, vm in enumerate(verse_matches):
            vnum_str = vm.group(2) or vm.group(3)  # group(2) for VerseOne, group(3) for VS
            verse_num = int(vnum_str)
            vstart = vm.end()
            vend = verse_matches[j + 1].start() if j + 1 < len(verse_matches) else len(chap_text)

            vtext_raw = chap_text[vstart:vend]
            vtext = strip_tex(vtext_raw)

            ref = f"{book_num}.{chap_num}.{verse_num}"
            verses[ref] = vtext

    return verses


def parse_swete_txt(path: Path) -> Dict[str, str]:
    """
    Parse a Swete .txt file of the form:

        1.1.1 ΕΝ
        1.1.1 APXH
        ...
        1.1.2 ἡ
        ...

    Returns dict: "1.1.1" -> "ΕΝ APXH ...".
    """
    verses: Dict[str, List[str]] = {}

    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 2:
                # If there's no word after the reference, skip it
                continue

            ref = parts[0]
            word = " ".join(parts[1:])
            verses.setdefault(ref, []).append(word)

    # Join word tokens into a verse string
    return {ref: " ".join(words) for ref, words in verses.items()}


def detect_book_info(swete_path: Path) -> Tuple[int, str]:
    """
    Try to detect (book_num, book_name) from the Swete filename and contents.

    - Filename pattern like "01.Genesis.txt" or "01.Genesis"
      -> book_num = 1, book_name = "Genesis"
    - Fallback: first non-empty verse reference's first number is book_num.
    """
    stem = swete_path.stem  # e.g. "01.Genesis"
    book_num = None
    book_name = None

    # Try to parse from filename
    if "." in stem:
        maybe_num, maybe_name = stem.split(".", 1)
        if maybe_num.isdigit():
            book_num = int(maybe_num)
            book_name = maybe_name
    else:
        # If no dot, maybe stem is just the name, e.g. "Genesis"
        book_name = stem

    # Try to read first verse reference to get book_num if needed
    if book_num is None:
        with swete_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                first = line.split()[0]  # e.g. "1.1.1"
                if "." in first:
                    first_part = first.split(".")[0]
                    if first_part.isdigit():
                        book_num = int(first_part)
                        break

    if book_num is None:
        book_num = 0  # Fallback; user can override with --book-num

    if not book_name:
        # Very last fallback
        book_name = f"Book{book_num}"

    return book_num, book_name


# ---------- Comparison helpers ----------

def sort_verse_keys(keys: Iterable[str]) -> List[str]:
    """Sort keys like '1.1.10' numerically."""
    def key_fn(k: str):
        parts = k.split(".")
        out = []
        for p in parts:
            if p.isdigit():
                out.append(int(p))
            else:
                out.append(0)
        return tuple(out)
    return sorted(keys, key=key_fn)


def compare_verses_simple(
    brenton: Dict[str, str],
    swete: Dict[str, str],
) -> Dict[str, str]:
    """
    Simple, fast comparison with no LLM.

    For each verse:
      - If missing in one edition, notes that.
      - If present in both, computes:
          - similarity ratio (difflib)
          - a small list of tokens unique to each edition
    """
    all_keys = sort_verse_keys(set(brenton.keys()) | set(swete.keys()))
    results: Dict[str, str] = {}

    for vid in all_keys:
        b = brenton.get(vid)
        s = swete.get(vid)

        if b is None and s is None:
            # shouldn't happen, but be safe
            diff = "Missing in both editions."
        elif b is None:
            diff = "Missing in Brenton; present in Swete."
        elif s is None:
            diff = "Present in Brenton; missing in Swete."
        else:
            # Normalize for comparison (case-insensitive)
            norm_b = b.lower()
            norm_s = s.lower()

            if norm_b == norm_s:
                diff = "IDENTICAL (case-insensitive)."
            else:
                ratio = difflib.SequenceMatcher(None, norm_b, norm_s).ratio()
                tokens_b = set(norm_b.split())
                tokens_s = set(norm_s.split())
                only_b = sorted(tokens_b - tokens_s)
                only_s = sorted(tokens_s - tokens_b)
                parts = [f"similarity={ratio:.3f}"]

                if only_b:
                    parts.append("only_in_brenton=[" + ", ".join(only_b[:8]) + "]")
                if only_s:
                    parts.append("only_in_swete=[" + ", ".join(only_s[:8]) + "]")

                diff = "; ".join(parts)

        results[vid] = diff

    return results


# ---------- Optional: LLM-based comparison with LangChain + Gemini ----------

def chunks(seq: List, n: int) -> Iterable[List]:
    """Yield successive n-sized chunks from a list."""
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def compare_verses_gemini(
    brenton: Dict[str, str],
    swete: Dict[str, str],
    model_name: str = "gemini-1.5-pro",
    api_key_env: str = "GEMINI_API_KEY",
    batch_size: int = 20,
) -> Dict[str, str]:
    """
    LLM-based comparison using LangChain + Gemini.

    NOTE:
      - Requires `langchain-google-genai` (and its dependencies) installed.
      - Requires your Gemini API key in the environment variable specified by `api_key_env`.

    This function:
      - Packs verses into batches
      - Asks the model for JSON describing differences
      - Returns a dict verse_id -> difference_summary
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as e:
        raise RuntimeError(
            "LangChain + Gemini not available. Install `langchain-google-genai` first."
        ) from e

    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RuntimeError(
            f"Environment variable {api_key_env} is not set. "
            "Set your Gemini API key there."
        )

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.0,
    )

    verse_pairs = []
    all_keys = sort_verse_keys(set(brenton.keys()) | set(swete.keys()))

    for vid in all_keys:
        verse_pairs.append((vid, brenton.get(vid), swete.get(vid)))

    results: Dict[str, str] = {}

    import json  # local import so script still runs without LLM

    for batch in chunks(verse_pairs, batch_size):
        # Build prompt for this batch
        lines = []
        lines.append(
            "You are comparing two Greek Bible editions (Brenton and Swete). "
            "For each verse, you will receive an id and the text from each edition."
        )
        lines.append(
            "For each verse, output a JSON object with:\n"
            '  "verse_id": string,\n'
            '  "status": "identical" | "different" | "missing",\n'
            '  "difference_summary": short English description of differences.\n'
            "If a verse is missing in one edition, note which one."
        )
        lines.append("Return ONLY a JSON array, no extra text.")
        lines.append("")
        lines.append("DATA:")
        for vid, b, s in batch:
            lines.append(f"VERSE {vid}")
            lines.append(f"Brenton: {b if b is not None else '<MISSING>'}")
            lines.append(f"Swete: {s if s is not None else '<MISSING>'}")
            lines.append("")

        prompt = "\n".join(lines)

        response = llm.invoke(prompt)
        # Depending on the version, response.content might be a list or string
        content = getattr(response, "content", None)
        if isinstance(content, list):
            content = "".join(str(c) for c in content)
        if content is None:
            content = str(response)

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Gemini response could not be parsed as JSON.\nResponse was:\n{content}"
            ) from e

        if not isinstance(data, list):
            raise RuntimeError(f"Expected a JSON array from Gemini, got: {type(data)}")

        for item in data:
            vid = item.get("verse_id")
            summary = item.get("difference_summary", "").strip()
            status = item.get("status", "").strip()
            if not summary:
                summary = status or "No difference summary provided."
            if vid:
                results[vid] = summary

    # Ensure all verses have some entry (fallback to simple if needed)
    simple_fallback = compare_verses_simple(brenton, swete)
    for vid in all_keys:
        if vid not in results:
            results[vid] = "[LLM missing] " + simple_fallback[vid]

    return results


# ---------- Writing output ----------

def write_tsv(
    out_path: Path,
    brenton: Dict[str, str],
    swete: Dict[str, str],
    diffs: Dict[str, str],
):
    """
    Write tab-delimited file:

        verse_id    brenton_text    swete_text    diff_summary
    """
    all_keys = sort_verse_keys(set(brenton.keys()) | set(swete.keys()))

    with out_path.open("w", encoding="utf-8") as f:
        f.write("verse_id\tbrenton\tswete\tdiff\n")
        for vid in all_keys:
            b = (brenton.get(vid) or "").replace("\t", " ")
            s = (swete.get(vid) or "").replace("\t", " ")
            d = (diffs.get(vid) or "").replace("\t", " ")

            f.write(f"{vid}\t{b}\t{s}\t{d}\n")


# ---------- CLI ----------

def main():
    parser = argparse.ArgumentParser(
        description="Compare Brenton (.tex) and Swete (.txt) LXX editions."
    )
    parser.add_argument(
        "--brenton",
        required=True,
        type=Path,
        help="Path to Brenton LaTeX file (e.g., GEN_src.tex).",
    )
    parser.add_argument(
        "--swete",
        required=True,
        type=Path,
        help="Path to Swete text file (e.g., 01.Genesis.txt).",
    )
    parser.add_argument(
        "--mode",
        choices=["simple", "gemini"],
        default="simple",
        help="Comparison mode: 'simple' (default) or 'gemini' (LLM-based).",
    )
    parser.add_argument(
        "--book-num",
        type=int,
        default=None,
        help="Override book number (e.g., 1 for Genesis). "
             "If omitted, tries to infer from Swete file.",
    )
    parser.add_argument(
        "--book-name",
        type=str,
        default=None,
        help="Override book name (e.g., 'Genesis'). "
             "If omitted, tries to infer from Swete file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output TSV path. If omitted, will be auto-named based on book num and name.",
    )
    parser.add_argument(
        "--gemini-model",
        type=str,
        default="gemini-1.5-pro",
        help="Gemini model name to use in LLM mode.",
    )
    parser.add_argument(
        "--gemini-key-env",
        type=str,
        default="GEMINI_API_KEY",
        help="Environment variable name holding the Gemini API key.",
    )
    parser.add_argument(
        "--gemini-batch-size",
        type=int,
        default=20,
        help="Number of verses per LLM request batch (LLM mode only).",
    )

    args = parser.parse_args()

    # Detect book info
    detected_num, detected_name = detect_book_info(args.swete)
    book_num = args.book_num if args.book_num is not None else detected_num
    book_name = args.book_name if args.book_name is not None else detected_name

    # Parse input files
    brenton_verses = parse_brenton_tex(args.brenton, book_num=book_num)
    swete_verses = parse_swete_txt(args.swete)

    # Compare
    if args.mode == "simple":
        diffs = compare_verses_simple(brenton_verses, swete_verses)
    else:
        diffs = compare_verses_gemini(
            brenton_verses,
            swete_verses,
            model_name=args.gemini_model,
            api_key_env=args.gemini_key_env,
            batch_size=args.gemini_batch_size,
        )

    # Decide output path
    if args.output is not None:
        out_path = args.output
    else:
        # Default: "<booknum>.<bookname>.diffs.tsv", using two-digit book number if possible
        num_str = f"{book_num:02d}" if isinstance(book_num, int) else str(book_num)
        safe_name = re.sub(r"\s+", "_", book_name)
        out_path = Path(f"{num_str}.{safe_name}.diffs.tsv")

    write_tsv(out_path, brenton_verses, swete_verses, diffs)

    print(f"Wrote differences to: {out_path}")


if __name__ == "__main__":
    main()