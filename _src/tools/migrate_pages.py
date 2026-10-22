"""One-off migration: every exported page that is not a book or author page
becomes a page record in _src/content/pages/<url path>/:

  index.json  title, extra <head>/script tags and named book lists
  index.html  the page's <main> element, with each run of book cards replaced
              by a slot such as <!--@cards select="catalogue:adult-titles-2026" wrap=li-->

The build fills slots from the book content, so a book edited in one place
updates every page that shows it.  Run from the repository root:
    python3 _src/tools/migrate_pages.py
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_src"))
from sitegen import content  # noqa: E402
from sitegen.html import prefix_for  # noqa: E402

OUT = ROOT / "_src/content/pages"
GENERATED_SECTIONS = ("books/", "authors/")

CARD = r'<article class="(group[^"]*)"><a class="lift block" href="(?:\.\./)*books/([^"/]+)/">.*?</article>'
WRAPS = {"li": ("<li>", "</li>"), "none": ("", "")}
RUN = re.compile(rf"(?:<li>{CARD}</li>)+|(?:{CARD})+", re.S)


def page_paths():
    for page in sorted(ROOT.glob("**/index.html")):
        rel = page.relative_to(ROOT).as_posix()
        path = rel[: -len("index.html")]
        if rel.startswith(("_src/", ".git/")):
            continue
        if path.count("/") == 2 and path.startswith(GENERATED_SECTIONS):
            continue  # rendered from books/ and authors/ content
        yield page, path


def selection(ctx, slugs):
    """Name the rule that picks exactly these books, or None for a hand-picked list."""
    order = list(ctx.books)
    if slugs == order:
        return "all"
    for key in ("catalogue", "imprint", "category"):
        for value in {b.get(key) for b in ctx.books.values()}:
            if value and slugs == [s for s, b in ctx.books.items() if b.get(key) == value]:
                return f"{key}:{value}"
    return None


def list_name(main_html, start, taken):
    label = re.findall(r'aria-label="([^"]+)"', main_html[max(0, start - 400):start])
    base = content.slugify(label[-1]) if label else "list"
    name, n = base, 2
    while name in taken:
        name, n = f"{base}-{n}", n + 1
    return name


def count_slots(ctx, path, fragment):
    """Replace title counts that must follow the content with <!--@count--> slots.

    Each pattern is checked against the real count first, so only numbers that
    are correct today become live; stale numbers stay as literal text.
    """
    labels = {c["label"]: c["slug"] for c in ctx.settings["categories"]}

    def counted(rule, number):
        kind, _, value = rule.partition(":")
        books = list(ctx.books) if rule == "all" else [s for s, b in ctx.books.items() if b.get(kind) == value]
        assert len(books) == int(number), (path, rule, number, len(books))
        return f'<!--@count select="{rule}"-->'

    def category_filter(m):
        slug = labels[html.unescape(m.group(1))]
        return m.group(0)[: -len(m.group(2)) - len("</span>")] + counted(f"category:{slug}", m.group(2)) + "</span>"

    if path == "books/":
        fragment = re.sub(r'title="([^"]+)">[^<]+</span><span class="text-xs text-ink-3 tabular-nums">(\d+)</span>',
                          category_filter, fragment)
        fragment = re.sub(r'(aria-live="polite" class="text-sm text-ink-2">)(\d+)( titles</p>)',
                          lambda m: m.group(1) + counted("all", m.group(2)) + m.group(3), fragment)
        fragment = re.sub(r"(Showing <!-- -->)(\d+)(<!-- --> of <!-- -->)(\d+)",
                          lambda m: m.group(1) + counted("all", m.group(2)) + m.group(3) + counted("all", m.group(4)),
                          fragment)
    if path == "":
        fragment = re.sub(r'(\?category=([a-z-]+)">(?:(?!</a>).)*?sm:inline">)(\d+)( titles</span>)',
                          lambda m: m.group(1) + counted(f"category:{m.group(2)}", m.group(3)) + m.group(4), fragment)
    catalogue = re.fullmatch(r"catalogues/([a-z0-9-]+-titles-\d{4})/", path)
    if catalogue:
        fragment = re.sub(r'(<h2 class="text-display-md">Titles in this catalogue</h2><p class="mt-3 text-\[0.9375rem\] '
                          r'leading-relaxed text-ink-2">)(\d+)( titles</p>)',
                          lambda m: m.group(1) + counted(f"catalogue:{catalogue.group(1)}", m.group(2)) + m.group(3),
                          fragment)
    return fragment


def refuse_to_overwrite(folder: Path):
    """These migrations ran once; content is edited by hand or in the admin panel
    from then on, so re-running would silently discard those edits."""
    if folder.exists() and any(folder.iterdir()) and "--force" not in sys.argv:
        sys.exit(f"{folder.relative_to(ROOT)} already has content; pass --force to overwrite it")


def main():
    refuse_to_overwrite(OUT)
    ctx = content.load(ROOT)
    count = 0
    for page, path in page_paths():
        source = page.read_text(encoding="utf-8")
        r = prefix_for(path)
        styles = source.find('assets/styles.css">') + len('assets/styles.css">')
        record = {
            "path": path,
            "title_html": re.search(r"<title>(.*?)</title>", source).group(1),
            "head_extra": source[styles:source.find("</head>")].replace(f'"{r}', '"~/') if r else source[styles:source.find("</head>")],
            "tail_extra": "",
            "lazy_logos": 'loading="lazy" width="720"' in source,
            "lists": {},
        }
        tail = source[source.find("</footer>"):]
        after_site_js = tail.find("defer></script>") + len("defer></script>")
        extra = tail[after_site_js:tail.find("<!-- Cloudflare")]
        record["tail_extra"] = extra.replace(f'"{r}', '"~/') if r else extra

        main_html = source[source.find("<main"):source.find("</main>") + len("</main>")]

        def to_slot(match):
            run = match.group(0)
            wrap = "li" if run.startswith("<li>") else "none"
            classes = set(re.findall(r'<article class="(group[^"]*)"><a class="lift block"', run))
            assert len(classes) == 1, (path, classes)
            slugs = re.findall(r'<a class="lift block" href="(?:\.\./)*books/([^"/]+)/">', run)
            rule = selection(ctx, slugs)
            if rule is None:
                name = list_name(main_html, match.start(), record["lists"])
                record["lists"][name] = slugs
                rule = f"list:{name}"
            article = classes.pop()
            attr = "" if article == "group" else f' article="{article}"'
            return f'<!--@cards select="{rule}" wrap={wrap}{attr}-->'

        fragment = count_slots(ctx, path, RUN.sub(to_slot, main_html))
        folder = OUT / path
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (folder / "index.html").write_text(fragment, encoding="utf-8")
        count += 1
    print(f"wrote {count} pages to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
