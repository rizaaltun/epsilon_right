"""Build the static site from _src/content/ into the repository root.

    python3 _src/build.py           write every generated page
    python3 _src/build.py --check   write nothing; report files whose generated
                                    output differs from what is on disk
    python3 _src/build.py --check --show books/x/index.html
                                    print where one file differs

Standard library only, so it runs anywhere with Python 3.9+.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sitegen import (authors, books, catalogues, content, events, meta, news, pages, publishers, seo,  # noqa: E402
                     services, shell)


def generate(ctx) -> dict:
    """Return {relative output path: file text} for everything the build owns."""
    out = {}
    for slug in ctx.books:
        path, text = books.render(ctx, slug)
        out[path + "index.html"] = text
    for slug in ctx.authors:
        path, text = authors.render(ctx, slug)
        out[path + "index.html"] = text
    for slug in ctx.news:
        path, text = news.render(ctx, slug)
        out[path + "index.html"] = text
    for slug in ctx.events:
        path, text = events.render(ctx, slug)
        out[path + "index.html"] = text
    for slug in ctx.publishers:
        path, text = publishers.render(ctx, slug)
        out[path + "index.html"] = text
    for slug in ctx.services:
        path, text = services.render(ctx, slug)
        out[path + "index.html"] = text
    for slug in ctx.catalogues:
        path, text = catalogues.render(ctx, slug)
        out[path + "index.html"] = text
    for record in pages.load_pages(ctx.root):
        path, text = pages.render(ctx, record)
        out[path + "index.html"] = text
    out["assets/meta.json"] = meta.render(ctx)
    page_paths = [rel[: -len("index.html")] for rel in out if rel.endswith("index.html")]
    out["sitemap.xml"] = seo.sitemap(ctx, page_paths)
    out["robots.txt"] = seo.robots(ctx)
    out["llms.txt"] = llms_txt(ctx)
    out["404.html"] = not_found(ctx)
    return out


def llms_txt(ctx) -> str:
    cat_labels = {c["slug"]: c["label"] for c in ctx.settings["categories"]}
    sections = [
        ("Start here", [("About the group", "about-us/", "history, imprints and the rights team"),
                        ("All titles", "books/", f"{len(ctx.books)} titles available for translation, with filters"),
                        ("Catalogues", "catalogues/", "rights catalogues to read online or download as PDF"),
                        ("Contact", "contact/", "rights enquiries")]),
        ("Catalogues", [(c["title"], f"catalogues/{s}/", c.get("category", "")) for s, c in catalogues.ordered(ctx)]),
        ("Books by category", [(label, f"books/?category={slug}", f"{len(ctx.books_in('category', slug))} titles")
                               for slug, label in cat_labels.items()]),
        ("Publishers", [(p["name"], f"publishers/{s}/", f"{len(publishers.titles(ctx, s))} titles") for s, p in publishers.ordered(ctx)]),
        ("Services", [(v["title"], f"services/{s}/", v.get("summary", "")) for s, v in services.ordered(ctx)]),
        ("News", [(n["title"], f"news/{s}/", str(n["date"])) for s, n in news.ordered(ctx)[:10]]),
        ("Fairs and events", [(e["title"], f"fairs-events/{s}/", e.get("start_date", "")) for s, e in
                              events.upcoming(ctx) + events.past(ctx)]),
        ("Authors", [(ctx.authors[s]["name"], f"authors/{s}/", "") for s in publishers.authors_alphabetical(ctx)]),
        ("Titles", [(b["title"], f"books/{s}/", f'{b["author"]} — {cat_labels.get(b["category"], "")}'
                     + (f' — English title: {b["english_title"]}' if b.get("english_title") and b["english_title"] != b["title"] else ""))
                    for s, b in ctx.books.items()]),
    ]
    return seo.llms(ctx, sections)


def not_found(ctx) -> str:
    """GitHub Pages serves /404.html for unknown URLs at any depth, so its links are absolute."""
    r = "/"
    main = (
        '<main id="main" class="flex-1"><section class="py-14 md:py-20"><div class="shell"><div class="max-w-2xl">'
        '<p class="eyebrow mb-4">Page not found</p><h1 class="text-display-lg">This page has moved or no longer exists</h1>'
        '<p class="mt-5 text-lg leading-relaxed text-ink-2">The title you are looking for may still be in the catalogue.</p>'
        f'<div class="mt-9 flex flex-wrap gap-3"><a class="btn btn-primary" href="{r}books/">Browse all titles</a>'
        f'<a class="btn btn-outline" href="{r}">Home page</a><a class="btn btn-outline" href="{r}contact/">Contact us</a>'
        "</div></div></div></section></main>"
    )
    meta = seo.Seo(path="404.html", title="Page not found", noindex=True)
    return shell.page(r, "404/", ctx.settings, f'Page not found — {ctx.settings["site_name"]}', main,
                      seo_html=seo.head_tags(ctx, meta))


def orphans(files: dict) -> list:
    """Generated pages on disk whose content was deleted.

    Only <section>/<slug>/index.html under the content-driven sections is owned
    by the build this way; nothing else is ever removed.
    """
    stale = []
    for section in ("books", "authors", "news", "fairs-events", "publishers", "services", "catalogues"):
        for page in sorted((ROOT / section).glob("*/index.html")):
            rel = page.relative_to(ROOT).as_posix()
            if rel not in files:
                stale.append(rel)
    return stale


def first_difference(a: str, b: str, context: int = 160) -> str:
    i = next((n for n, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return (
        f"  at character {i} (generated {len(a)}, on disk {len(b)})\n"
        f"  generated: …{a[max(0, i - context):i + context]!r}\n"
        f"  on disk:   …{b[max(0, i - context):i + context]!r}"
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="compare with the files on disk, write nothing")
    parser.add_argument("--show", metavar="PATH", help="with --check, print the first difference in PATH")
    args = parser.parse_args(argv)

    ctx = content.load(ROOT, write=not args.check)
    files = generate(ctx)

    if args.check:
        differing = []
        for rel, text in files.items():
            target = ROOT / rel
            current = target.read_text(encoding="utf-8") if target.exists() else None
            if current != text:
                differing.append(rel)
                if args.show == rel:
                    print(first_difference(text, current or ""))
        stale = orphans(files)
        print(f"{len(files) - len(differing)} of {len(files)} generated files match the files on disk")
        for rel in differing[:40]:
            print("  differs:", rel)
        if len(differing) > 40:
            print(f"  … and {len(differing) - 40} more")
        for rel in stale:
            print("  would remove:", rel)
        return 1 if differing or stale else 0

    written = 0
    for rel, text in files.items():
        target = ROOT / rel
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            written += 1
    removed = orphans(files)
    for rel in removed:
        page = ROOT / rel
        page.unlink()
        if not any(page.parent.iterdir()):
            page.parent.rmdir()
    print(f"generated {len(files)} files, {written} changed, {len(removed)} removed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
