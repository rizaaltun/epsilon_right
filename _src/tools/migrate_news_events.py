"""One-off migration: the three exported news articles and the Frankfurt fair
become content in _src/content/news/ and _src/content/events/, and the pages
that list them get slots instead of hand-written cards.

Run from the repository root:  python3 _src/tools/migrate_news_events.py
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
NEWS = ROOT / "_src/content/news"
EVENTS = ROOT / "_src/content/events"


def one(pattern, source, flags=re.S):
    m = re.search(pattern, source, flags)
    if not m:
        raise ValueError(pattern)
    return m.group(1)


def text(fragment):
    return html.unescape(fragment)


def fragment(path):
    return (PAGES / path / "index.html").read_text(encoding="utf-8")


def gallery(source):
    block = re.search(r'aria-label="Gallery">(.*?)</ul>', source, re.S)
    if not block:
        return []
    return [{"image": "/" + src.replace("../", ""), "alt": text(alt)}
            for alt, src in re.findall(r'<img alt="([^"]*)"[^>]*src="([^"]+)"', block.group(1))]


def write(folder, slug, data):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{slug}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if NEWS.exists() and "--force" not in sys.argv:
        sys.exit("_src/content/news already exists; pass --force to overwrite it")
    home = fragment("")

    def home_excerpt(slug):
        card = one(rf'<a class="block" href="news/{slug}/">(.*?)</article>', home)
        return text(re.findall(r"<p[^>]*>(.*?)</p>", card)[-1])

    for slug in ("frankfurt-book-fair-2026-return", "sharjah-booksellers-conference-2026"):
        src = fragment(f"news/{slug}")
        hero = re.search(r'mx-auto mt-12 max-w-3xl rounded-md" style="aspect-ratio:([^"]+)"><img alt="([^"]*)"[^>]*src="([^"]+)"', src)
        title = text(one(r'<h1 class="mt-5 text-display-lg">(.*?)</h1>', src))
        item = {
            "title": title,
            "date": one(r'<time dateTime="([^"]+)"', src),
            "category": text(one(r'<span class="chip chip-accent">(.*?)</span>', src)),
            "byline": text(one(r'gap-y-1 text-sm text-ink-3"><span>(.*?)</span>', src)),
            "excerpt": home_excerpt(slug),
            "image": "/" + hero.group(3).replace("../", ""),
            "image_ratio": hero.group(1),
            "show_image": True,
            "body": convert(one(r'<div class="prose-editorial">(.*?)</div>', src)),
            "gallery": gallery(src),
        }
        if text(hero.group(2)) != title:
            item["image_alt"] = text(hero.group(2))
        source_note = re.search(r'<div class="mt-10 border-t border-rule pt-6"><p class="text-xs text-ink-3">(.*?)</p>', src)
        if source_note:
            item["source"] = text(source_note.group(1))
        write(NEWS, slug, item)

    slug = "publishers-weekly-sharjah-2026"
    src = fragment(f"news/{slug}")
    card = one(rf'<a class="block" href="news/{slug}/">(.*?)</article>', home)
    write(NEWS, slug, {
        "title": text(one(r'<h1 class="mt-5 text-display-lg">(.*?)</h1>', src)),
        "date": one(r'<time datetime="([^"]+)"', src),
        "category": text(one(r'<span class="chip chip-accent">(.*?)</span>', src)),
        "byline": text(one(r"</time> · (.*?)</p>", src)),
        "excerpt": home_excerpt(slug),
        "image": "/" + one(r'<img src="([^"]+)"', card),
        "image_alt": text(one(r'<img src="[^"]+" alt="([^"]*)"', card)),
        "image_ratio": "3/2",
        "show_image": False,
        "body": convert(one(r'<div class="prose-editorial mt-12">(.*?)</div>', src)),
        "gallery": [],
    })

    slug = "frankfurter-buchmesse-2026"
    src = fragment(f"fairs-events/{slug}")
    index = fragment("fairs-events")
    venue, city, country = text(one(r'<p class="mt-4 text-lg text-ink-2">(.*?)</p>', src)).split(", ")
    write(EVENTS, slug, {
        "title": text(one(r'<h1 class="mt-3 text-display-lg">(.*?)</h1>', src)),
        "start_date": "2026-10-07",
        "end_date": "2026-10-11",
        "venue": venue,
        "city": city,
        "country": country,
        "stand": text(one(r"Stand <!-- -->(.*?)</span>", src)),
        "summary": text(one(r'<p class="clamp-2 mt-2 max-w-2xl text-sm leading-relaxed text-ink-2">(.*?)</p>', index)),
        "body": convert(one(r'<div class="prose-editorial mt-8 measure">(.*?)</div>', src)),
        "image": "/" + one(r'lg:sticky lg:top-28" style="aspect-ratio:4/5"><img alt="[^"]*"[^>]*src="([^"]+)"', src).replace("../", ""),
        "image_alt": text(one(r'lg:sticky lg:top-28" style="aspect-ratio:4/5"><img alt="([^"]*)"', src)),
        # The export linked to https://example.org (a placeholder) and showed
        # template placeholder images as its gallery; both are left out.
        "website": "https://www.buchmesse.de/en",
        "gallery": [],
    })
    assert "7–11 October 2026" in src

    # Listing pages: hand-written cards become slots.
    home = re.sub(r'(<div id="news-track" class="news-track"[^>]*>).*?(</div></div></div></div></section>)',
                  r'\1<!--@news-cards limit=3-->\2', home, count=1, flags=re.S)
    home = re.sub(r'(<div class="hb-aside"><div class="hb-pane-inner">).*?(</div></div><div class="hb-gauge")',
                  r"\1<!--@event-aside-->\2", home, count=1, flags=re.S)
    (PAGES / "index.html").write_text(home, encoding="utf-8")

    news_index = fragment("news")
    news_index = news_index.replace("Latest · 3 articles", "Latest · <!--@news-count--> articles")
    news_index = re.sub(r'(<div id="news-track" class="news-track"[^>]*>).*?(</div></div></div></section>)',
                        r"\1<!--@news-cards-->\2", news_index, count=1, flags=re.S)
    (PAGES / "news/index.html").write_text(news_index, encoding="utf-8")

    events_index = re.sub(r'<section id="upcoming".*?</section>', "<!--@event-sections-->", index, count=1, flags=re.S)
    (PAGES / "fairs-events/index.html").write_text(events_index, encoding="utf-8")

    # The article and event pages are now rendered from content.
    for path in ("news/frankfurt-book-fair-2026-return", "news/sharjah-booksellers-conference-2026",
                 "news/publishers-weekly-sharjah-2026", "fairs-events/frankfurter-buchmesse-2026"):
        shutil.rmtree(PAGES / path)
    print("migrated 3 news articles and 1 event")


if __name__ == "__main__":
    sys.exit(main())
