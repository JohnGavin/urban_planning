#!/usr/bin/env python3
"""
Extract the text of the source PDFs in raw/ into one plain-text file per page.

Why: reading-comprehension passages (site/data/passages.json) must be grounded in
the source documents. Each passage lists short verbatim "evidence" quotes with a
document + page; validate_questions.py checks that every quote really occurs on
that page of the extracted text. The model never transcribes the PDFs by hand.

Output layout (committed, so the check works without the PDF tools):
    raw/text/<doc-key>/p001.txt, p002.txt, ...
Page numbers are PDF page indices starting at 1 (the page number a PDF viewer shows).

Usage:
    python3 scripts/extract_pdf_text.py                 # all known documents
    python3 scripts/extract_pdf_text.py --doc oerek     # one document
    python3 scripts/extract_pdf_text.py --check         # exit 1 if output is stale/missing

Backend: pypdf if importable, else the `pdftotext` command (poppler).
Exit codes: 0 ok, 1 check failed, 2 usage, 3 no extraction backend available.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# One home for the document keys used in passages.json "evidence" entries.
DOCS = {
    'oerek': 'raw/Stoff_OEREK-2030 (1).pdf',
    'studienplan': 'raw/Stoff_Studienplan_Bachelorstudium_Raumplanung_und_Raumordnung_2022.pdf',
    'info': 'raw/Info_Raumplanung_Info_AV_RPL_TU_2026.pdf',
}
OUT_DIR = 'raw/text'


def normalise(text):
    """Join hyphenated line breaks, collapse whitespace. Used for page files and quote matching."""
    text = text.replace('­', '')                 # soft hyphen
    # The ÖREK layout marks a line-break hyphen as " -" (space before it): "Ge -\nmeinden".
    # Real compounds ("Städte- und") have no space before the hyphen and are kept.
    text = re.sub(r'(\w) -[ \t]*\n[ \t]*(\w)', r'\1\2', text)
    text = re.sub(r'[ \t\r\f\v]+', ' ', text)
    text = re.sub(r'\s*\n\s*', '\n', text)
    return text.strip() + '\n'


def extract_pages(pdf_path):
    try:
        import pypdf  # noqa: F401
        reader = pypdf.PdfReader(pdf_path)
        return [p.extract_text() or '' for p in reader.pages], 'pypdf'
    except ImportError:
        pass
    if shutil.which('pdftotext') and shutil.which('pdfinfo'):
        info = subprocess.run(['pdfinfo', pdf_path], capture_output=True, text=True, check=True).stdout
        n = int(re.search(r'^Pages:\s+(\d+)', info, re.MULTILINE).group(1))
        pages = []
        for i in range(1, n + 1):
            out = subprocess.run(['pdftotext', '-f', str(i), '-l', str(i), pdf_path, '-'],
                                 capture_output=True, text=True, check=True).stdout
            pages.append(out)
        return pages, 'pdftotext'
    return None, None


def page_files(key):
    return os.path.join(ROOT, OUT_DIR, key)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--doc', choices=sorted(DOCS), help='only this document')
    ap.add_argument('--check', action='store_true', help='compare with committed output, do not write')
    args = ap.parse_args()

    keys = [args.doc] if args.doc else sorted(DOCS)
    stale = []
    for key in keys:
        pdf = os.path.join(ROOT, DOCS[key])
        if not os.path.exists(pdf):
            print(f'MISSING PDF: {DOCS[key]}', file=sys.stderr)
            stale.append(key)
            continue
        pages, backend = extract_pages(pdf)
        if pages is None:
            print('No extraction backend: install pypdf or poppler (pdftotext).', file=sys.stderr)
            sys.exit(3)
        outdir = page_files(key)
        if not args.check:
            os.makedirs(outdir, exist_ok=True)
        for i, raw in enumerate(pages, start=1):
            text = normalise(raw)
            path = os.path.join(outdir, f'p{i:03d}.txt')
            if args.check:
                if not os.path.exists(path) or open(path, encoding='utf-8').read() != text:
                    stale.append(f'{key} p{i}')
            else:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text)
        print(f'{key}: {len(pages)} pages via {backend} -> {OUT_DIR}/{key}/')
    if args.check:
        if stale:
            print(f'STALE/MISSING: {len(stale)} page(s), e.g. {stale[:5]}', file=sys.stderr)
            sys.exit(1)
        print('OK: extracted text matches the PDFs')


if __name__ == '__main__':
    main()
