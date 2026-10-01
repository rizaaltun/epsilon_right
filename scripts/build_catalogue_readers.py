"""Import verified small PDF parts and build the five static catalogue readers."""
from pathlib import Path
import hashlib
import html
import json
import re
import shutil
import fitz
from PIL import Image

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


def reader(title, pdf, slug, pages, ratio, revision):
    return f'''<section id="catalogue-reader" aria-label="Interactive catalogue">
<div class="catalogue-reader" data-catalogue-reader data-title="{html.escape(title, quote=True)}" data-pages="../../assets/images/catalogues/pages/{slug}-{revision}/" data-count="{pages}" data-ratio="{ratio:.6f}" data-return="../" role="dialog" aria-modal="true" aria-label="{html.escape(title, quote=True)}" tabindex="0">
<div class="reader-book" tabindex="0" aria-label="Catalogue pages"></div>
<div class="reader-cover-fallback"><img src="../../assets/images/catalogues/{slug}.webp" alt="{html.escape(title, quote=True)} cover" fetchpriority="high"></div>
<button class="reader-exit" type="button" aria-label="Close catalogue">×</button>
<button class="reader-edge prev" type="button" data-prev aria-label="Previous pages" disabled>‹</button>
<button class="reader-edge next" type="button" data-next aria-label="Next pages" disabled>›</button>
<p class="reader-status" role="status" aria-live="polite">…</p>
<p class="reader-help">Drag a page corner or swipe to turn. Use left and right arrows. Double-click a page to read it enlarged. Escape closes the catalogue.</p>
<div class="reader-magnifier" hidden><img alt="Enlarged catalogue page"><button type="button" aria-label="Close enlarged page">×</button></div>
<noscript><a href="../../assets/catalogues/{pdf}">Open PDF catalogue</a></noscript></div></section>'''


def main():
    import_parts()
    staged = ROOT / "scripts/reader-assets"
    if staged.exists():
        (ROOT/"assets/vendor").mkdir(exist_ok=True)
        for name in ["flipbook.css", "flipbook.js"]:
            shutil.copyfile(staged/name, ROOT/"assets"/name)
            shutil.copyfile(staged/name, ROOT/"assets"/name.replace('flipbook.', 'catalogue-reader-v3.'))
        for name in ["page-flip.browser.js", "page-flip.LICENSE"]:
            shutil.copyfile(staged/name, ROOT/"assets/vendor"/name)
    template = (ROOT / 'catalogues/adult-titles-2026/index.html').read_text()
    cards = []
    performance = []
    version = hashlib.sha256((ROOT/'assets/flipbook.js').read_bytes() + (ROOT/'assets/flipbook.css').read_bytes()).hexdigest()[:10]
    images = ROOT / 'assets/images/catalogues'
    images.mkdir(parents=True, exist_ok=True)
    for slug, title, category, filename in CATALOGUES:
        pdf = ROOT / 'assets/catalogues' / filename
        assert pdf.exists(), f'Missing PDF {pdf}'
        revision = hashlib.sha256(pdf.read_bytes()).hexdigest()[:8]
        page_dir = images / 'pages' / (slug + '-' + revision)
        page_dir.mkdir(parents=True, exist_ok=True)
        with fitz.open(pdf) as document:
            pages = len(document)
            first = document[0]
            ratio = first.rect.height / first.rect.width
            for i, page in enumerate(document):
                target = page_dir / f'{i+1:03d}.webp'
                valid = False
                if target.exists():
                    try:
                        with Image.open(target) as checked:
                            checked.load()
                            valid = checked.width == 1800
                    except (OSError, ValueError):
                        pass
                if not valid:
                    rendered = page.get_pixmap(matrix=fitz.Matrix(1800/page.rect.width,1800/page.rect.width), alpha=False)
                    image = Image.frombytes('RGB', [rendered.width, rendered.height], rendered.samples)
                    image.save(target, 'WEBP', quality=90, method=3)
                with Image.open(target) as checked:
                    checked.load()
                    assert checked.width == 1800
            performance.append({'catalogue':slug,'pages':pages,'pdf_bytes':pdf.stat().st_size,'first_page_bytes':(page_dir/'001.webp').stat().st_size,'initial_three_page_bytes':sum((page_dir/f'{i+1:03d}.webp').stat().st_size for i in range(min(3,pages))),'all_page_images_bytes':sum(p.stat().st_size for p in page_dir.glob('*.webp'))})
            pixmap = first.get_pixmap(matrix=fitz.Matrix(700 / first.rect.width, 700 / first.rect.width))
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
            main = main[:position] + reader(title, filename, slug, pages, ratio, revision) + main[position:]
            source = re.sub(r'<main\b.*?</main>', lambda _: main, source, count=1, flags=re.S)
        else:
            source = template
            main = f'''<main id="main" class="flex-1"><section class="py-14 md:py-20"><div class="shell">
<nav aria-label="Breadcrumb" class="text-xs text-ink-3 mb-10"><a href="../../catalogues/">Catalogues</a> / {safe_title}</nav>
<div class="grid gap-10 lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)] lg:gap-16"><div class="cover aspect-3/4"><img src="{cover_url}" alt="{safe_title} cover" style="width:100%;height:100%;object-fit:contain" decoding="async"></div>
<div><p class="eyebrow">Books &amp; Publications</p><h1 class="mt-3 text-display-lg">{safe_title}</h1><p class="mt-5 text-ink-2">{pages} pages · 2026 · {html.escape(category)}</p>
<div class="mt-9 flex flex-wrap gap-3"><a href="#catalogue-reader" class="btn btn-primary">Read catalogue</a><a href="../../assets/catalogues/{filename}" class="btn btn-outline" download>Download ({pdf.stat().st_size/1_000_000:.1f} MB)</a></div></div></div></div></section>{reader(title, filename, slug, pages, ratio, revision)}</main>'''
            source = re.sub(r'<main\b.*?</main>', lambda _: main, source, count=1, flags=re.S)
            source = source.replace('Adult Titles 2026', safe_title).replace('/catalogues/adult-titles-2026', '/catalogues/' + slug)
        source = re.sub(r'<link[^>]*href="[^"]*assets/(?:flipbook.css|catalogue-reader-v3.css)[^"]*"[^>]*>', '', source)
        source = re.sub(r'<script[^>]*src="[^"]*assets/(?:flipbook.js|catalogue-reader-v3.js|vendor/page-flip.browser.js)[^"]*"[^>]*></script>', '', source)
        source = re.sub(r'<link[^>]*data-reader-preload[^>]*>', '', source)
        source = re.sub(r'<style id="catalogue-layout">.*?</style>', '', source, flags=re.S)
        source = source.replace('</head>', '<style id="catalogue-layout">html,body{background:#faf9f5!important;color-scheme:light}.catalogue-reader:not(.is-open){display:none!important}.catalogue-reader.is-open{display:grid!important;position:fixed!important;inset:0!important;width:100vw;height:100vh;background:#faf9f5!important}.catalogue-reader:fullscreen{background:#faf9f5!important}.catalogue-reader::backdrop{background:#faf9f5}</style></head>')
        source = source.replace('</head>', f'<link rel="stylesheet" href="../../assets/catalogue-reader-v3.css?v={version}"><link data-reader-preload rel="preload" as="image" href="../../assets/images/catalogues/{slug}.webp"></head>')
        source = source.replace('</body>', f'<script defer src="../../assets/vendor/page-flip.browser.js?v=2.0.7"></script><script defer src="../../assets/catalogue-reader-v3.js?v={version}"></script></body>')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        badge = '<span class="catalogue-new" style="position:absolute;top:12px;right:12px;background:#153f34;color:white;padding:5px 12px;border-radius:999px;font:600 12px Arial">New</span>' if slug in {'childrens-titles-2026', 'adult-titles-2026'} else ''
        cards.append(f'''<article class="group"><a class="block" href="../catalogues/{slug}/?reader=3"><div class="cover aspect-3/4" style="position:relative"><img src="../assets/images/catalogues/{slug}.webp" alt="{safe_title} cover" loading="lazy" decoding="async" style="width:100%;height:100%;object-fit:contain">{badge}</div><div class="mt-3.5"><h3 class="font-display text-[1.0625rem] leading-snug">{safe_title}</h3><p class="mt-1 text-[0.8125rem] text-ink-3">{html.escape(category)} · 2026 · {pages} pages</p></div></a></article>''')
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
    (ROOT/'assets/catalogues/reader-performance.json').write_text(json.dumps(performance,indent=2)+'\n')
    print(json.dumps(performance))
    print('Built five full-viewport readers with pre-rendered pages.')


if __name__ == '__main__':
    main()
