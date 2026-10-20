"""One-off migration: the five catalogue pages become content in
_src/content/catalogues/, the existing reader images are recorded in
assets/catalogues/readers.json, and /catalogues/ gets slots.

Run from the repository root:  python3 _src/tools/migrate_catalogues.py
"""
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from html_to_markdown import convert  # noqa: E402

PAGES = ROOT / "_src/content/pages"
OUT = ROOT / "_src/content/catalogues"


def main():
    if OUT.exists() and "--force" not in sys.argv:
        sys.exit("_src/content/catalogues already exists; pass --force to overwrite it")
    index_path = PAGES / "catalogues/index.html"
    index = index_path.read_text(encoding="utf-8")
    cards = re.findall(r'<article class="group"><a class="block" href="\.\./catalogues/([^/]+)/\?reader=3">(.*?)</article>', index, re.S)
    manifest = {}
    for order, (slug, card) in enumerate(cards, start=1):
        page = (PAGES / f"catalogues/{slug}/index.html").read_text(encoding="utf-8")
        category, year, pages = re.search(r'text-ink-3">(.*?) · (\d{4}) · (\d+) pages</p>', card).groups()
        category = html.unescape(category)
        pdf = re.search(r'<noscript><a href="\.\./\.\./([^"]+\.pdf)">', page).group(1)
        reader = re.search(r'data-pages="\.\./\.\./assets/images/catalogues/pages/[a-z0-9-]+-([0-9a-f]{8})/" data-count="(\d+)" '
                           r'data-ratio="([\d.]+)"', page)
        revision, count, ratio = reader.group(1), int(reader.group(2)), float(reader.group(3))
        assert hashlib.sha256((ROOT / pdf).read_bytes()).hexdigest()[:8] == revision, slug
        assert count == int(pages), slug
        description = re.search(r'<div class="prose-editorial mt-7">(.*?)</div>', page, re.S)
        item = {
            "title": html.unescape(re.search(r'<h1 class="mt-3 text-display-lg">(.*?)</h1>', page).group(1)),
            "category": category,
            "year": year,
            "description": convert(description.group(1)) if description else "",
            "pdf": "/" + pdf,
            "cover": "",
            "new": "catalogue-new" in card,
            "order": order,
        }
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{slug}.json").write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest[slug] = {"pdf": pdf, "revision": revision, "pages": count, "ratio": ratio}
        shutil.rmtree(PAGES / f"catalogues/{slug}")
    (ROOT / "assets/catalogues/readers.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    index = re.sub(r'(<p class="mt-3 text-\[0.9375rem\] leading-relaxed text-ink-2">)\d+ catalogues(</p>)',
                   r"\1<!--@catalogue-count-->\2", index, count=1)
    index = re.sub(r'(<div class="grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">).*?'
                   r'(</div></div></div></section>)', r"\1<!--@catalogue-cards-->\2", index, count=1, flags=re.S)
    index_path.write_text(index, encoding="utf-8")
    print(f"migrated {len(cards)} catalogues")


if __name__ == "__main__":
    sys.exit(main())
