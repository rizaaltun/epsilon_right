"""Make the small preview PDF for a book's English sample from the print files.

    python3 _src/tools/make_sample_preview.py INSIDE.pdf [COVER.pdf] OUT.pdf [--pages N]

Print PDFs are large (crop marks, bleed, 300 dpi images) and contain the whole
book. The site only shows a preview, so this keeps:

  * the front cover: the right-hand part of the cover spread (back | spine |
    front), taken from COVER.pdf or, without it, from a cover spread inside
    INSIDE.pdf;
  * the first quarter of the book's pages (a 32-page book shows 8), or N pages,
    always ending on a whole spread.

Every page is cut to its trim box and stored as a JPEG at the size the reader
shows, and the result is what goes to _src/samples/ (the site's build turns it
into the reader pages; see sitegen/samples.py for the format). Needs PyMuPDF
and Pillow.
"""

import argparse
import io
import sys
from collections import Counter

import fitz
from PIL import Image

WIDE = 1.3          # width / height at or above this: two pages side by side
SPREAD_TOLERANCE = 0.004
PAGE_PX = 1400      # pixels across one page, the size the reader shows


def _mode(values):
    return Counter(values).most_common(1)[0][0]


def trim(page):
    """The page's trim box; when the file has none, the rectangle its crop marks point to."""
    if page.trimbox != page.mediabox:
        return page.trimbox
    w, h = page.rect.width, page.rect.height
    top, bottom, left, right = set(), set(), set(), set()
    for drawing in page.get_drawings():
        for item in drawing["items"]:
            if item[0] != "l":
                continue
            a, b = item[1], item[2]
            if abs(a.x - b.x) < 0.5 and abs(a.y - b.y) <= 25:      # short vertical line
                x = round(a.x, 1)
                if min(a.y, b.y) < 1:
                    top.add(x)
                if max(a.y, b.y) > h - 1:
                    bottom.add(x)
            elif abs(a.y - b.y) < 0.5 and abs(a.x - b.x) <= 25:    # short horizontal line
                y = round(a.y, 1)
                if min(a.x, b.x) < 1:
                    left.add(y)
                if max(a.x, b.x) > w - 1:
                    right.add(y)
    xs, ys = sorted(top & bottom), sorted(left & right)
    if len(xs) >= 2 and len(ys) >= 2:
        return fitz.Rect(xs[0], ys[0], xs[-1], ys[-1])
    return page.trimbox


def sheets(doc):
    """[(page number, kind, trim rect)] with kind single, spread or cover (a cover spread)."""
    trims = [trim(doc[i]) for i in range(len(doc))]
    narrow = [t for t in trims if t.width / t.height < WIDE]
    if narrow:
        single, height = _mode(round(t.width, 1) for t in narrow), _mode(round(t.height, 1) for t in narrow)
    else:
        single, height = _mode(round(t.width, 1) for t in trims) / 2, _mode(round(t.height, 1) for t in trims)
    out = []
    for i, t in enumerate(trims):
        if t.width / t.height < WIDE:
            kind = "single"
        elif abs(t.width - 2 * single) / (2 * single) < SPREAD_TOLERANCE and abs(t.height - height) / height < 0.01:
            kind = "spread"
        else:
            kind = "cover"
        out.append((i, kind, t))
    return out, single, height


def front_cover(rect, single, height):
    """The front cover inside a cover spread: its right-hand part, one page wide."""
    if rect.width / rect.height < WIDE:
        return rect
    width = single * rect.height / height
    return fitz.Rect(rect.x1 - width, rect.y0, rect.x1, rect.y1)


def preview_sheets(inside, pages=None):
    """The interior sheets to keep: whole sheets until a quarter of the pages, ending on a spread."""
    book = [(i, kind, t) for i, kind, t in inside if kind != "cover"]
    total = sum(2 if kind == "spread" else 1 for _, kind, _ in book)
    want = pages or max(4, round(total / 4))
    # A single first page is a right-hand page; a book that opens on a spread starts on the left.
    offset = 1 if book and book[0][1] == "spread" else 0
    keep, count = [], 0
    for sheet in book:
        if count >= want and (count + offset) % 2 == 1:  # stop after a right-hand page
            break
        keep.append(sheet)
        count += 2 if sheet[1] == "spread" else 1
    return keep, count, total


def make(inside_path, cover_path, out_path, pages=None):
    inside = fitz.open(inside_path)
    layout, single, height = sheets(inside)
    if cover_path:
        cover_doc = fitz.open(cover_path)
        cover_src, cover_rect = cover_doc, front_cover(trim(cover_doc[0]), single, height)
    else:
        spreads = [(i, t) for i, kind, t in layout if kind == "cover"]
        if not spreads:
            sys.exit(f"{inside_path}: no cover file and no cover spread inside; give COVER.pdf")
        cover_src, cover_rect = inside, front_cover(spreads[0][1], single, height)
        cover_doc = None
    keep, count, total = preview_sheets(layout, pages)
    out = fitz.open()
    _add(out, cover_src[0 if cover_doc else spreads[0][0]], cover_rect, single)
    for i, kind, t in keep:
        _add(out, inside[i], t, single)
    out.save(out_path, garbage=4, deflate=True)
    return {"pages": count, "book_pages": total, "sheets": len(keep)}


def _add(out, src_page, clip, single):
    """Copy one sheet as a JPEG, PAGE_PX pixels per page width (print files embed the
    whole book's images in every page, so copying the vector page keeps them all)."""
    scale = PAGE_PX / single
    pix = src_page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
    buffer = io.BytesIO()
    Image.frombytes("RGB", [pix.width, pix.height], pix.samples).save(buffer, "JPEG", quality=88, optimize=True)
    page = out.new_page(width=clip.width, height=clip.height)
    page.insert_image(page.rect, stream=buffer.getvalue())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("files", nargs="+", help="INSIDE.pdf [COVER.pdf] OUT.pdf")
    parser.add_argument("--pages", type=int, help="pages to keep (default: a quarter of the book)")
    args = parser.parse_args()
    if len(args.files) not in (2, 3):
        parser.error("give INSIDE.pdf [COVER.pdf] OUT.pdf")
    inside_pdf, cover_pdf, out_pdf = (args.files[0], None, args.files[1]) if len(args.files) == 2 else args.files
    print(make(inside_pdf, cover_pdf, out_pdf, args.pages))
