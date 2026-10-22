"""One-off migration: the six exported publisher pages become content in
_src/content/publishers/, and /publishers/, /representations/ and /authors/
get slots so their cards and counts follow the content.

Run from the repository root:  python3 _src/tools/migrate_publishers.py
"""
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
OUT = ROOT / "_src/content/publishers"


def one(pattern, source, flags=re.S):
    m = re.search(pattern, source, flags)
    if not m:
        raise ValueError(pattern)
    return m.group(1)


def sub_once(pattern, repl, source):
    result, n = re.subn(pattern, repl, source, count=1, flags=re.S)
    if n != 1:
        raise ValueError(f"not found: {pattern}")
    return result


def main():
    if OUT.exists() and "--force" not in sys.argv:
        sys.exit("_src/content/publishers already exists; pass --force to overwrite it")
    OUT.mkdir(parents=True, exist_ok=True)
    index = (PAGES / "publishers/index.html").read_text(encoding="utf-8")
    order = re.findall(r'href="\.\./publishers/([^/"]+)/"', index)
    for position, slug in enumerate(order, start=1):
        page = (PAGES / f"publishers/{slug}/index.html").read_text(encoding="utf-8")
        record = json.loads((PAGES / f"publishers/{slug}/index.json").read_text(encoding="utf-8"))
        pub = {
            "name": html.unescape(one(r'<h1 class="text-display-lg">(.*?)</h1>', page)),
            "imprint": one(r'<!--@cards select="imprint:([^"]+)"', page),
            "country": html.unescape(one(r'<p class="mt-3 text-\[0.9375rem\] text-ink-3">(.*?)</p>', page)),
            "summary": "",
            "description": convert(one(r'<div class="prose-editorial">(.*?)</div>', page)),
            "logo": "",
            "email": "",
            "website": "",
            "featured": False,
            "order": position,
        }
        logo = re.search(r'<img alt="[^"]*" width="(\d+)" height="(\d+)"[^>]*src="([^"]+)"', page)
        if logo:
            pub["logo"] = "/" + logo.group(3).replace("../", "")
            pub["logo_width"], pub["logo_height"] = int(logo.group(1)), int(logo.group(2))
        assert record["title_html"].startswith(html.escape(pub["name"], quote=False)), slug
        assert "mailto:pelin@epsilonyayingrubu.com" in page, slug
        (OUT / f"{slug}.json").write_text(json.dumps(pub, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shutil.rmtree(PAGES / f"publishers/{slug}")

    # /publishers/
    index = sub_once(r'(<ul class="max-h-64 space-y-1.5 overflow-y-auto pr-1">).*?(</ul>)', r"\1<!--@publisher-countries-->\2", index)
    index = sub_once(r'<div class="py-4"><label class="flex cursor-pointer[^"]*"><input[^>]*/><span class="flex-1">Featured</span>.*?</div>',
                     "<!--@featured-filter kind=publishers-->", index)
    index = sub_once(r'(aria-live="polite" class="text-sm text-ink-2">)\d+( publishers</p>)', r"\1<!--@publisher-count-->\2", index)
    index = sub_once(r'(<p class="mb-6 text-sm text-ink-3">).*?(</p>)', r"\1<!--@publisher-summary-->\2", index)
    index = sub_once(r'(<ul class="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">).*?(</ul>)', r"\1<!--@publisher-cards-->\2", index)
    index = sub_once(r"Showing <!-- -->\d+<!-- --> of <!-- -->\d+",
                     "Showing <!-- --><!--@publisher-count--><!-- --> of <!-- --><!--@publisher-count-->", index)
    (PAGES / "publishers/index.html").write_text(index, encoding="utf-8")

    # /representations/
    rep = (PAGES / "representations/index.html").read_text(encoding="utf-8")
    rep = sub_once(r'(<p class="eyebrow mb-3">)\d+(<!-- --> <!-- -->authors</p>)', r"\1<!--@author-count-->\2", rep)
    rep = sub_once(r'(<div class="rail" role="group" aria-label="Authors" tabindex="0">).*?(</div></div></div></section>)',
                   r"\1<!--@top-authors limit=8-->\2", rep)
    rep = sub_once(r'(<p class="eyebrow mb-3">)\d+(<!-- --> <!-- -->publishers</p>)', r"\1<!--@publisher-count-->\2", rep)
    rep = sub_once(r'(<ul class="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">).*?(</ul>)', r"\1<!--@publisher-cards order=titles-->\2", rep)
    (PAGES / "representations/index.html").write_text(rep, encoding="utf-8")

    # /authors/: every author (the export showed 24 behind a "Load more" button that did nothing)
    authors = (PAGES / "authors/index.html").read_text(encoding="utf-8")
    authors = sub_once(r'(<span class="flex-1">Has titles</span><span class="text-xs text-ink-3 tabular-nums">)\d+(</span>)',
                       r"\1<!--@authors-with-titles-->\2", authors)
    authors = sub_once(r'<div class="py-4"><label class="flex cursor-pointer[^"]*"><input[^>]*/><span class="flex-1">Featured</span>.*?</div>',
                       "<!--@featured-filter kind=authors-->", authors)
    authors = sub_once(r'(<nav aria-label="Jump to letter" class="mb-6"><ul class="flex flex-wrap gap-1">).*?(</ul></nav>)',
                       r"\1<!--@author-letters-->\2", authors)
    authors = sub_once(r'(aria-live="polite" class="text-sm text-ink-2">)\d+( authors</p>)', r"\1<!--@author-count-->\2", authors)
    authors = sub_once(r'(<ul class="grid grid-cols-2 gap-x-5 gap-y-10 sm:grid-cols-3 lg:grid-cols-4">).*?(</ul>)',
                       r"\1<!--@author-cards-->\2", authors)
    authors = sub_once(r'<p class="text-xs text-ink-3">Showing <!-- -->\d+<!-- --> of <!-- -->\d+</p><button type="button" class="btn btn-outline">Load more</button>',
                       '<p class="text-xs text-ink-3">Showing <!-- --><!--@author-count--><!-- --> of <!-- --><!--@author-count--></p>', authors)
    (PAGES / "authors/index.html").write_text(authors, encoding="utf-8")
    print(f"migrated {len(order)} publishers; /publishers/, /representations/ and /authors/ now use slots")


if __name__ == "__main__":
    sys.exit(main())
