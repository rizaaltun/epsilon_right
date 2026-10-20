"""One-off migration: read the exported book pages + assets/meta.json and write
one JSON content file per book into _src/content/books/.

Run from the repository root:  python3 _src/tools/migrate_books.py
The build (_src/build.py --check) then proves the content reproduces the pages.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "_src/content/books"

DL_FIELDS = {
    "Original title": "original_title",
    "Original language": "original_language",
    "English title": "english_title",
    "Imprint": "imprint",
    "Pages": "pages",
    "Publication year": "publication_year",
    "Illustrator": "illustrator",
    "Age group": "age_group",
}


def text(fragment: str) -> str:
    return html.unescape(fragment)


def one(pattern: str, source: str, flags=0) -> str:
    match = re.search(pattern, source, flags)
    if not match:
        raise ValueError(f"pattern not found: {pattern}")
    return match.group(1)


def refuse_to_overwrite(folder: Path):
    """These migrations ran once; content is edited by hand or in the admin panel
    from then on, so re-running would silently discard those edits."""
    if folder.exists() and any(folder.iterdir()) and "--force" not in sys.argv:
        sys.exit(f"{folder.relative_to(ROOT)} already has content; pass --force to overwrite it")


def main():
    refuse_to_overwrite(OUT)
    meta = json.loads((ROOT / "assets/meta.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for order, (slug, item) in enumerate(meta.items(), start=1):
        page = (ROOT / "books" / slug / "index.html").read_text(encoding="utf-8")
        main_html = page[page.find("<main"):page.find("More in this category")]

        book = {
            "title": text(one(r'<h1 class="text-display-lg">(.*?)</h1>', main_html)),
            "author": text(re.sub(r"<[^>]+>", "", one(r'<p class="mt-5 text-\[0.9375rem\] text-ink-2">(.*?)</p>', main_html))),
            "category": one(r'<a href="\.\./\.\./books/\?category=([^"]+)"><span class="chip">', main_html),
            "catalogue": one(r'href="\.\./\.\./catalogues/([^/]+)/#catalogue-reader"', main_html),
            "order": order,
        }
        cover = re.search(r'<img alt="[^"]*— cover"[^>]*?src="\.\./\.\./(assets/images/covers/[^"]+)"', main_html)
        book["cover"] = cover.group(1) if cover else ""
        book["square_cover"] = bool(item.get("sq"))
        paragraphs = re.findall(r"<p>(.*?)</p>", one(r'<div class="prose-editorial">(.*?)</div>', main_html, re.S), re.S)
        book["description"] = "\n\n".join(text(p) for p in paragraphs)
        for label, value in re.findall(r'<dt class="text-ink-3">(.*?)</dt><dd class="text-ink">(.*?)</dd>', main_html, re.S):
            book[DL_FIELDS[text(label)]] = text(value)
        book["rights"] = text(one(r'<p class="mt-3 text-sm leading-relaxed text-ink-2">(.*?)</p>', main_html, re.S))
        book["rights_sold"] = item["l"]
        book["featured"] = item["f"]
        book["new"] = item["n"]

        # Cross-checks against meta.json, so a silent mismatch can't slip through.
        assert book["title"] == item["t"], slug
        assert book["author"] == item["a"], slug
        assert book["category"] == item["c"], slug
        expected_cover = "/" + book["cover"] if book["cover"] else None
        assert item["p"] == expected_cover, slug

        (OUT / f"{slug}.json").write_text(json.dumps(book, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(meta)} books to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
