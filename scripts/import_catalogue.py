"""Assemble a staged YA PDF, verify its identity, and activate catalogue links.

Small binary parts avoid connector request-size limits. A missing manifest is a
normal no-op after a successful import; staged files are removed on completion.
"""
from pathlib import Path
import hashlib
import json
import re
import fitz

ROOT = Path(__file__).resolve().parents[1]


def main():
    staging = ROOT / '.github/ya-upload'
    manifest_path = staging / 'manifest.json'
    if not manifest_path.exists():
        print('No staged catalogue to import.')
        return
    manifest = json.loads(manifest_path.read_text())
    parts = manifest['parts']
    assert parts and len(parts) == len(set(parts))
    assert all(re.fullmatch(r'\d{3}\.part', name) for name in parts)
    data = b''.join((staging / name).read_bytes() for name in parts)
    assert len(data) == manifest['bytes'], 'PDF size mismatch'
    assert hashlib.sha256(data).hexdigest() == manifest['sha256'], 'PDF hash mismatch'
    with fitz.open(stream=data, filetype='pdf') as pdf:
        assert len(pdf) == 18 and not pdf.is_encrypted
        assert 'YOUNG' in pdf[0].get_text()
        for page in pdf:
            assert page.get_text().strip(), 'Missing catalogue text'
    target = ROOT / 'assets/catalogues/ya-catalogue-2026.pdf'
    target.write_bytes(data)
    meta = json.loads((ROOT / 'assets/meta.json').read_text())
    pages = [ROOT / 'catalogues/young-adult-titles-2026/index.html']
    pages += [ROOT / 'books' / slug / 'index.html' for slug, item in meta.items()
              if item['c'] == 'young-adult']
    count = 0
    for page in pages:
        original = page.read_text()

        def activate(match):
            nonlocal count
            link = match[0]
            if 'aria-disabled="true"' not in link:
                return link
            count += 1
            link = re.sub(r' (?:aria-disabled|tabindex|style)="[^"]*"', '', link)
            link = link.replace('<a ', '<a href="../../assets/catalogues/ya-catalogue-2026.pdf" ', 1)
            return re.sub(r'Download \([\d.]+ MB\)', f'Download ({len(data)/1_000_000:.1f} MB)', link)

        updated = re.sub(r'<a\b[^>]*>[^<]*(?:Open catalogue|Download)[^<]*</a>', activate, original)
        if updated != original:
            page.write_text(updated)
    for name in parts:
        (staging / name).unlink()
    manifest_path.unlink()
    staging.rmdir()
    print(f'Imported {len(data)} bytes, verified SHA-256, activated {count} links.')


if __name__ == '__main__':
    main()
