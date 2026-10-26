"""English samples: a preview of a book in the page-turning reader, opened by
"Read an English Sample" on its book page.

A book lists its samples in "english_samples":
    [{"pdf": "/_src/samples/<id>.pdf"}]                       one book
    [{"pdf": "...", "title": "A Line"}, {"pdf": ..., ...}]    a series page

The PDF holds only the preview (_src/tools/make_sample_preview.py makes it from
the print files): page 1 is the front cover, or a cover spread (back | spine |
front) whose right-hand page is used; then the pages to show, in order, each
one page or a spread of two. In the reader the cover stands alone, the pages
face each other as in print (a single first page is a right-hand page), and a
closing page points to the rights enquiry.

The PDFs stay under _src/ (Jekyll does not publish folders starting with "_"),
so only page images are on the site. As for the catalogue reader (catalogues.py)
they are made with PyMuPDF + Pillow when a PDF changes, into
assets/images/samples/<id>-<revision>/NNN.webp (001 = cover), and recorded in
assets/images/samples/readers.json.
"""

import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

from .html import esc

MANIFEST = "assets/images/samples/readers.json"
PAGES_DIR = "assets/images/samples"
PAGE_PX = 1400  # image width of one page
WIDE = 1.3      # width / height at or above this: two pages side by side
ANCHOR = "english-sample"


def _manifest(ctx) -> dict:
    if not hasattr(ctx, "_samples"):
        path = Path(ctx.root, MANIFEST)
        ctx._samples = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return ctx._samples


def _render(ctx, sample_id, pdf, revision):
    try:
        import fitz
        from PIL import Image
    except ImportError:
        return None
    page_dir = Path(ctx.root, PAGES_DIR, f"{sample_id}-{revision}")
    page_dir.mkdir(parents=True, exist_ok=True)
    with fitz.open(pdf) as document:
        trims = [page.trimbox for page in document]
        inner = trims[1:] or trims
        narrow = [t for t in inner if t.width / t.height < WIDE]
        if narrow:
            single = Counter(round(t.width, 1) for t in narrow).most_common(1)[0][0]
            height = Counter(round(t.height, 1) for t in narrow).most_common(1)[0][0]
        else:
            single = Counter(round(t.width, 1) for t in inner).most_common(1)[0][0] / 2
            height = Counter(round(t.height, 1) for t in inner).most_common(1)[0][0]
        size = (PAGE_PX, round(PAGE_PX * height / single))
        images = []

        def image(page, clip):
            scale = PAGE_PX / single
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
            return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        cover = trims[0]
        if cover.width / cover.height >= WIDE:
            width = single * cover.height / height
            cover = fitz.Rect(cover.x1 - width, cover.y0, cover.x1, cover.y1)
        images.append(image(document[0], cover))
        # A book whose first page is a single sheet opens on a right-hand page, so the
        # reader puts a blank inside cover before it; one that opens on a spread does not.
        opens_single = len(trims) > 1 and trims[1].width / trims[1].height < WIDE
        for page, trim in zip(list(document)[1:], trims[1:]):
            picture = image(page, trim)
            if trim.width / trim.height >= WIDE:
                half = picture.width // 2
                images += [picture.crop((0, 0, half, picture.height)), picture.crop((half, 0, picture.width, picture.height))]
            else:
                images.append(picture)
    for n, picture in enumerate(images, 1):
        picture.resize(size, Image.LANCZOS).save(page_dir / f"{n:03d}.webp", "WEBP", quality=85, method=4)
    for old in Path(ctx.root, PAGES_DIR).glob(f"{sample_id}-*"):
        if old != page_dir and old.is_dir() and len(old.name) == len(sample_id) + 9:
            shutil.rmtree(old)
    return {"pdf": str(Path(pdf).relative_to(ctx.root).as_posix()), "revision": revision, "pages": len(images),
            "ratio": round(size[1] / size[0], 6), "blank": opens_single}


def _info(ctx, sample_id, pdf_path):
    """{revision, pages, ratio} for the sample's PDF, rendering images if needed; None if unavailable."""
    readers = _manifest(ctx)
    pdf = Path(ctx.root, pdf_path.lstrip("/"))
    if not pdf.is_file():
        print(f"warning: English sample {pdf_path} not found", file=sys.stderr)
        return None
    revision = hashlib.sha256(pdf.read_bytes()).hexdigest()[:8]
    info = readers.get(sample_id)
    if info and info["revision"] == revision:
        return info
    if ctx.write:
        info = _render(ctx, sample_id, pdf, revision)
        if info:
            readers[sample_id] = info
            Path(ctx.root, MANIFEST).parent.mkdir(parents=True, exist_ok=True)
            Path(ctx.root, MANIFEST).write_text(json.dumps(readers, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return info
    print(f"warning: English sample {pdf_path}: reader images need PyMuPDF and Pillow; built without it", file=sys.stderr)
    return None


def for_book(ctx, slug) -> list:
    """[(anchor, label, sample id, info)] for the book's samples that can be shown."""
    book = ctx.books[slug]
    entries = [s for s in book.get("english_samples") or [] if s.get("pdf")]
    out = []
    for n, sample in enumerate(entries, 1):
        sample_id = Path(sample["pdf"]).stem
        info = _info(ctx, sample_id, sample["pdf"])
        if info:
            anchor = ANCHOR if len(entries) == 1 else f"{ANCHOR}-{n}"
            out.append((anchor, sample.get("title") or "", sample_id, info))
    return out


def buttons(samples) -> str:
    if len(samples) == 1:
        return f'<a href="#{samples[0][0]}" class="btn btn-primary w-full">Read an English Sample</a>'
    links = "".join(f'<a href="#{anchor}" class="btn btn-primary w-full">{esc(label)}</a>' for anchor, label, _, _ in samples)
    return f'<p class="eyebrow mt-4">Read an English Sample</p>{links}<span class="mt-2"></span>'


def readers(r, book_title, enquire_href, samples) -> str:
    out = ""
    for anchor, label, sample_id, info in samples:
        title = esc(f"{book_title}: {label}" if label else book_title)
        out += (
            f'<div class="catalogue-reader sample-reader" id="{anchor}" data-sample-reader data-title="{title} — '
            f'English sample" data-pages="{r}{PAGES_DIR}/{sample_id}-{info["revision"]}/" data-count="{info["pages"]}" '
            f'data-ratio="{info["ratio"]:.6f}"{" data-blank" if info.get("blank") else ""} role="dialog" aria-modal="true" aria-label="{title} — English sample" '
            'tabindex="0"><div class="reader-book" tabindex="0" aria-label="Sample pages"></div><div '
            f'class="reader-cover-fallback"><img src="{r}{PAGES_DIR}/{sample_id}-{info["revision"]}/001.webp" '
            f'alt="{title} cover" loading="lazy"></div><button class="reader-exit" type="button" aria-label="Close '
            'sample">×</button><button class="reader-edge prev" type="button" data-prev aria-label="Previous pages" '
            'disabled>‹</button><button class="reader-edge next" type="button" data-next aria-label="Next pages" '
            'disabled>›</button><p class="reader-status" role="status" aria-live="polite">…</p><p class="reader-help">'
            'Drag a page corner or swipe to turn. Use left and right arrows. Double-click a page to read it enlarged. '
            'Escape closes the sample.</p><div class="reader-magnifier" hidden><img alt="Enlarged sample page"><button '
            'type="button" aria-label="Close enlarged page">×</button></div><template data-end><div class="sample-end">'
            '<p class="sample-end-eyebrow">End of the sample</p><p class="sample-end-title">Would you like to read '
            f'more?</p><p class="sample-end-text">The full English PDF is available for publishers.</p><a '
            f'class="sample-end-link" href="{enquire_href}">Enquire about rights</a></div></template></div>'
        )
    return out


def asset_version(ctx) -> str:
    root = Path(ctx.root, "assets")
    return hashlib.sha256(b"".join((root / name).read_bytes() for name in
                                   ("sample-reader.js", "sample-reader.css", "catalogue-reader-v3.css"))).hexdigest()[:10]


def head_extra(ctx) -> str:
    v = asset_version(ctx)
    return (f'<link rel="stylesheet" href="~/assets/catalogue-reader-v3.css?v={v}">'
            f'<link rel="stylesheet" href="~/assets/sample-reader.css?v={v}">')


def tail_extra(ctx) -> str:
    return ('<script defer src="~/assets/vendor/page-flip.browser.js?v=2.0.7"></script>'
            f'<script defer src="~/assets/sample-reader.js?v={asset_version(ctx)}"></script>')


def stale(ctx) -> tuple:
    """(manifest entries, image folders) of samples no book lists any more."""
    used = {Path(s["pdf"]).stem for book in ctx.books.values() for s in book.get("english_samples") or [] if s.get("pdf")}
    readers = _manifest(ctx)
    entries = [sample_id for sample_id in readers if sample_id not in used]
    # Folders are <id>-<revision>; older revisions of a sample in use are replaced when it renders.
    folders = sorted(p for p in Path(ctx.root, PAGES_DIR).glob("*-*") if p.is_dir() and p.name[:-9] not in used)
    return entries, folders


def remove_stale(ctx) -> int:
    entries, folders = stale(ctx)
    readers = _manifest(ctx)
    for sample_id in entries:
        del readers[sample_id]
    if entries:
        Path(ctx.root, MANIFEST).write_text(json.dumps(readers, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for folder in folders:
        shutil.rmtree(folder)
    return len(entries) + len(folders)
