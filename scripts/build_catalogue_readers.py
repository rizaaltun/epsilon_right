"""Import verified small PDF parts and build the five static catalogue readers."""
from pathlib import Path
import hashlib
import html
import json
import re
import fitz

ROOT = Path(__file__).resolve().parents[1]
CATALOGUES = [
    ('childrens-titles-2026', "Children's Titles 2026", "Children's", 'children-catalogue-2026.pdf'),
    ('adult-titles-2026', 'Adult Titles 2026', 'Adult', 'adult-catalogue-2026.pdf'),
    ('young-adult-titles-2026', 'Young Adult Titles 2026', 'Young Adult', 'ya-catalogue-2026.pdf'),
    ('adult-catalogue-2026', 'Adult Catalogue 2026', 'Adult', 'adult-full-catalogue-2026.pdf'),
    ('children-catalogue-2026', "Children's Catalogue 2026", "Children's", 'children-full-catalogue-2026.pdf'),
]


def import_parts():
    stage = ROOT / '.github/catalogue-upload'
    path = stage / 'manifest.json'
    if not path.exists():
        return
    records = json.loads(path.read_text())
    pending = []
    for record in records:
        assert record['path'] in {f'assets/catalogues/{c[3]}' for c in CATALOGUES[3:]}
        assert len(record['parts']) == len(set(record['parts']))
        assert all(re.fullmatch(r'[a-z0-9-]+-\d{3}\.part', p) for p in record['parts'])
        data = b''.join((stage / p).read_bytes() for p in record['parts'])
        assert len(data) == record['bytes']
        assert hashlib.sha256(data).hexdigest() == record['sha256']
        with fitz.open(stream=data, filetype='pdf') as document:
            assert len(document) == record['pages'] and not document.is_encrypted
        pending.append((record, data))
    # Validate both catalogues before replacing either destination.
    for record, data in pending:
        (ROOT / record['path']).write_bytes(data)
        for part in record['parts']:
            (stage / part).unlink()
        print('Imported original attached PDF:', record['path'], len(data), record['sha256'])
    path.unlink()
    stage.rmdir()


def reader(title, pdf):
    return f'''<section id="catalogue-reader" class="shell" aria-label="Interactive catalogue">
<div class="catalogue-reader" data-catalogue-reader data-pdf="../../assets/catalogues/{pdf}" tabindex="0" aria-busy="true">
<div class="reader-top"><h2>Browse the catalogue</h2><div class="reader-tools">
<button type="button" data-zoom aria-pressed="false">Zoom in</button><button type="button" data-fullscreen>Full screen</button>
<a href="../../assets/catalogues/{pdf}" target="_blank" rel="noopener noreferrer">Open PDF</a><a href="../../assets/catalogues/{pdf}" download>Download PDF</a></div></div>
<div class="reader-stage"><div class="reader-book" aria-label="{html.escape(title, quote=True)} pages"></div></div>
<div class="reader-bottom"><button type="button" data-prev disabled aria-label="Previous pages">← Previous</button>
<form class="reader-jump" data-jump><label>Page <input type="number" min="1" value="1" required aria-label="Go to page"></label><span>of <span data-total>…</span></span><button type="submit">Go</button></form>
<button type="button" data-next disabled aria-label="Next pages">Next →</button></div>
<p class="reader-status" role="status" aria-live="polite">Preparing catalogue…</p><p class="reader-hint">Use the arrows, left/right keys or swipe to turn the pages.</p>
<noscript><p>Enable JavaScript for page turning, or use the PDF links above.</p></noscript></div></section>'''


def main():
    import_parts()
    template = (ROOT / 'catalogues/adult-titles-2026/index.html').read_text()
    cards = []
    images = ROOT / 'assets/images/catalogues'
    images.mkdir(parents=True, exist_ok=True)
    for slug, title, category, filename in CATALOGUES:
        pdf = ROOT / 'assets/catalogues' / filename
        assert pdf.exists(), f'Missing PDF {pdf}'
        with fitz.open(pdf) as document:
            pages = len(document)
            first = document[0]
            pixmap = first.get_pixmap(matrix=fitz.Matrix(700 / first.rect.width, 700 / first.rect.width))
            from PIL import Image
            cover = Image.frombytes('RGB', [pixmap.width, pixmap.height], pixmap.samples)
            cover.save(images / (slug + '.webp'), 'WEBP', quality=88, method=6)
        path = ROOT / 'catalogues' / slug / 'index.html'
        cover_url = '../../assets/images/catalogues/' + slug + '.webp'
        safe_title = html.escape(title)
        if path.exists():
            source = path.read_text()
            # Remove only our earlier reader if this script is rerun.
            source = re.sub(r'<section id="catalogue-reader".*?</section>', '', source, flags=re.S)
            main = re.search(r'<main\b.*?</main>', source, re.S)[0]
            main = re.sub(r'(<img\b[^>]*\bsrc=")[^"]*("[^>]*>)', lambda m: m[1]+cover_url+m[2], main, count=1)
            main = re.sub(r'<a\b[^>]*>Open catalogue</a>', '<a href="#catalogue-reader" class="btn btn-primary">Read catalogue</a>', main)
            main = re.sub(r'Download \([\d.]+ MB\)', f'Download ({pdf.stat().st_size/1_000_000:.1f} MB)', main)
            # The reader belongs after the catalogue introduction, before title cards.
            position = main.index('</section>') + len('</section>')
            main = main[:position] + reader(title, filename) + main[position:]
            source = re.sub(r'<main\b.*?</main>', lambda _: main, source, count=1, flags=re.S)
        else:
            source = template
            main = f'''<main id="main" class="flex-1"><section class="py-14 md:py-20"><div class="shell">
<nav aria-label="Breadcrumb" class="text-xs text-ink-3 mb-10"><a href="../../catalogues/">Catalogues</a> / {safe_title}</nav>
<div class="grid gap-10 lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)] lg:gap-16"><div class="cover aspect-3/4"><img src="{cover_url}" alt="{safe_title} cover" style="width:100%;height:100%;object-fit:contain" decoding="async"></div>
<div><p class="eyebrow">Books &amp; Publications</p><h1 class="mt-3 text-display-lg">{safe_title}</h1><p class="mt-5 text-ink-2">{pages} pages · 2026 · {html.escape(category)}</p>
<div class="mt-9 flex flex-wrap gap-3"><a href="#catalogue-reader" class="btn btn-primary">Read catalogue</a><a href="../../assets/catalogues/{filename}" class="btn btn-outline" download>Download ({pdf.stat().st_size/1_000_000:.1f} MB)</a></div></div></div></div></section>{reader(title, filename)}</main>'''
            source = re.sub(r'<main\b.*?</main>', lambda _: main, source, count=1, flags=re.S)
            source = source.replace('Adult Titles 2026', safe_title).replace('/catalogues/adult-titles-2026', '/catalogues/' + slug)
        if 'assets/flipbook.css' not in source:
            source = source.replace('</head>', '<link rel="stylesheet" href="../../assets/flipbook.css"></head>')
        if 'assets/flipbook.js' not in source:
            source = source.replace('</body>', '<script type="module" src="../../assets/flipbook.js"></script></body>')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        cards.append(f'''<article class="group"><a class="block" href="../catalogues/{slug}/"><div class="cover aspect-3/4"><img src="../assets/images/catalogues/{slug}.webp" alt="{safe_title} cover" loading="lazy" decoding="async" style="width:100%;height:100%;object-fit:contain"></div><div class="mt-3.5"><h3 class="font-display text-[1.0625rem] leading-snug">{safe_title}</h3><p class="mt-1 text-[0.8125rem] text-ink-3">{html.escape(category)} · 2026 · {pages} pages</p></div></a></article>''')
    index = ROOT / 'catalogues/index.html'
    source = index.read_text()
    source = re.sub(r'<div class="grid grid-cols-2[^>]*>.*?</div></div></div></section>', '<div class="grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">' + ''.join(cards) + '</div></div></div></section>', source, count=1, flags=re.S)
    source = re.sub(r'\d+ catalogues', '5 catalogues', source)
    index.write_text(source)
    # Book-level catalogue links now lead to the reader. Download remains there.
    by_pdf = {c[3]:c[0] for c in CATALOGUES}
    for path in (ROOT / 'books').rglob('index.html'):
        source = path.read_text()
        def link(match):
            return f'<a href="../../catalogues/{by_pdf[match[1]]}/#catalogue-reader" class="btn btn-outline w-full">Read catalogue</a>'
        updated = re.sub(r'<a\b[^>]*href="../../assets/catalogues/([^"/]+\.pdf)"[^>]*>Download catalogue</a>', link, source)
        if updated != source:
            path.write_text(updated)
    print('Built five readers; attached Adult and Children catalogues are last. No New badges.')


if __name__ == '__main__':
    main()
