"""Hand-built pages stored as a <main> fragment plus a small JSON record.

Slots in a fragment are filled from content at build time:
  <!--@cards select="RULE" wrap=li|none [article="classes"]-->
      RULE: all | catalogue:<slug> | imprint:<name> | category:<slug> | list:<name>
      (list names refer to the page record's "lists", or to the JSON file
      named by its "lists_file", e.g. settings/home.json for the home page)
  <!--@count select="RULE"-->   the number of books RULE selects
  <!--@news-cards [limit=N]-->   news cards, newest first
  <!--@news-count-->             the number of news articles
  <!--@event-sections-->         the Upcoming / Past lists of fairs & events
  <!--@event-aside-->            the hero card on the home page (a fair or the latest news)
  <!--@publisher-cards [order=titles]-->, <!--@publisher-count-->, <!--@publisher-summary-->,
  <!--@publisher-countries-->    publisher cards, count, summary line and country filter
  <!--@author-cards-->, <!--@author-count-->, <!--@top-authors limit=N-->, <!--@author-letters-->,
  <!--@authors-with-titles-->    author cards (A–Z), count, most-published rail, A–Z jump list
  <!--@featured-filter kind=publishers|authors-->  the "Featured" filter row, if any are featured

Before the slots are filled, the fragment is rendered as a template (see
sitegen/template.py) with the page's editable texts (texts.json next to the
page record) and the shared settings: {{stats.items}}, {{contact.…}}, {{site.…}}.
  <!--@service-cards-->          all service cards
  <!--@catalogue-cards-->, <!--@catalogue-count-->   catalogue cards and count on /catalogues/
  <!--@blog-cards [limit=N]-->, <!--@blog-count-->     blog post cards (pinned first, then newest) and count
A record with "requires": "blog" is only built while the blog has posts.
"""

import json
import re
from pathlib import Path

import html

from . import blog, catalogues, events, news, publishers, seo, services, shell, template
from .components import book_card
from .html import prefix_for

COUNT = re.compile(r'<!--@count select="([^"]+)"-->')
OTHER = re.compile(r"<!--@(news-cards|news-count|event-sections|event-aside|publisher-cards|publisher-count|"
                   r"publisher-summary|publisher-countries|author-cards|author-count|top-authors|author-letters|"
                   r"authors-with-titles|featured-filter|service-cards|catalogue-cards|catalogue-count|blog-cards|blog-count)((?: \w+=\S+?)*)-->")
SLOT = re.compile(r'<!--@cards select="([^"]+)" wrap=(li|none)(?: article="([^"]+)")?-->')


def load_pages(root: str) -> list:
    pages = []
    base = Path(root, "_src/content/pages")
    for record_file in sorted(base.glob("**/index.json")):
        record = json.loads(record_file.read_text(encoding="utf-8"))
        record["main"] = (record_file.parent / "index.html").read_text(encoding="utf-8")
        texts_file = record_file.parent / "texts.json"
        record["texts"] = json.loads(texts_file.read_text(encoding="utf-8")) if texts_file.exists() else {}
        if record.get("lists_file"):
            lists_file = Path(root, "_src/content", record["lists_file"])
            record["lists"] = {**record.get("lists", {}), **json.loads(lists_file.read_text(encoding="utf-8"))}
        pages.append(record)
    return pages


def select(ctx, record: dict, rule: str) -> list:
    if rule == "all":
        return list(ctx.books.items())
    kind, _, value = rule.partition(":")
    if kind == "list":
        return [(s, ctx.books[s]) for s in record["lists"][value] if s in ctx.books]
    if kind in ("catalogue", "imprint", "category"):
        return ctx.books_in(kind, value)
    raise ValueError(f"unknown card selection {rule!r} on {record['path'] or 'home'}")


def render(ctx, record: dict) -> tuple:
    path = record["path"]
    r = prefix_for(path)

    def fill(match):
        rule, wrap, article = match.group(1), match.group(2), match.group(3) or "group"
        cards = (book_card(ctx, r, s, b, article_class=article) for s, b in select(ctx, record, rule))
        return "".join(f"<li>{c}</li>" if wrap == "li" else c for c in cards)

    main = template.render(record["main"], record["texts"], {"@r": r}, ctx.shared)
    main = SLOT.sub(fill, main)
    main = COUNT.sub(lambda m: str(len(select(ctx, record, m.group(1)))), main)

    def other(match):
        name, args = match.group(1), dict(a.split("=", 1) for a in match.group(2).split())
        if name == "news-cards":
            return news.cards(ctx, r, args.get("limit"))
        if name == "news-count":
            return str(len(ctx.news))
        if name == "event-sections":
            return events.sections(ctx, r)
        if name == "event-aside":
            return events.aside(ctx, r)
        if name == "publisher-cards":
            return publishers.cards(ctx, r, args.get("order", "panel"))
        if name == "publisher-count":
            return str(len(ctx.publishers))
        if name == "publisher-summary":
            return publishers.summary_line(ctx)
        if name == "publisher-countries":
            return publishers.country_filter(ctx)
        if name == "author-cards":
            return publishers.author_cards(ctx, r)
        if name == "author-count":
            return str(len(ctx.authors))
        if name == "top-authors":
            return publishers.top_authors(ctx, r, int(args.get("limit", 8)))
        if name == "author-letters":
            return publishers.letter_nav(ctx)
        if name == "service-cards":
            return services.cards(ctx, r)
        if name == "blog-cards":
            return blog.cards(ctx, r, args.get("limit"))
        if name == "blog-count":
            n = len(ctx.blog)
            return f"{n} post" + ("" if n == 1 else "s")
        if name == "catalogue-cards":
            return catalogues.index_cards(ctx, r)
        if name == "catalogue-count":
            n = len(ctx.catalogues)
            return f"{n} catalogue" + ("" if n == 1 else "s")
        if name == "authors-with-titles":
            return str(publishers.authors_with_titles(ctx))
        return publishers.featured_filter(ctx, args.get("kind", "publishers"))

    main = OTHER.sub(other, main)
    texts = record["texts"]
    title_html = record["title_html"]
    if texts.get("seo_title"):
        title_html = html.escape(texts["seo_title"], quote=False)
    return path, shell.page(
        r, path, ctx.settings, title_html, main,
        head_extra=record["head_extra"], tail_extra=record["tail_extra"], lazy_logos=record["lazy_logos"],
        seo_html=seo.head_tags(ctx, page_seo(ctx, record)),
    )


def page_seo(ctx, record: dict):
    path, texts = record["path"], record["texts"]
    name = texts.get("title") or html.unescape(record["title_html"]).split(" — ")[0]
    if path == "":
        name = ctx.settings["site_name"]
    description = seo.describe(texts, texts.get("intro"), texts.get("lead"), texts.get("hero_text"),
                               ctx.settings.get("default_description"))
    if path == "":
        description = seo.describe(texts, ctx.settings.get("default_description"))
    image = texts.get("hero_image") or ""
    org = seo.organization(ctx)
    page_url = seo.url(ctx, path)
    if path == "":
        jsonld = [org, {"@type": "WebSite", "name": ctx.settings["site_name"], "url": page_url, "inLanguage": "en",
                        "publisher": {"@id": org["@id"]}}]
    elif path == "about-us/":
        jsonld = [org, {"@type": "AboutPage", "name": name, "url": page_url, "mainEntity": {"@id": org["@id"]}}]
    elif path == "contact/":
        contact = ctx.shared.get("contact", {})
        org["contactPoint"] = [{"@type": "ContactPoint", "contactType": "rights enquiries",
                                "email": contact.get("rights_email") or ctx.settings["email"],
                                **({"telephone": contact["phone"]} if contact.get("phone") else {})}]
        jsonld = [org, {"@type": "ContactPage", "name": name, "url": page_url, "mainEntity": {"@id": org["@id"]}}]
    else:
        trail = [("Home", "")]
        parent = path.rsplit("/", 2)[0] + "/" if path.count("/") > 1 else ""
        if parent:
            trail.append((parent.strip("/").replace("-", " ").title(), parent))
        trail.append((name, path))
        jsonld = [{"@type": "CollectionPage", "name": name, "url": page_url, "description": description,
                   "isPartOf": {"@type": "WebSite", "name": ctx.settings["site_name"], "url": seo.url(ctx, "")}},
                  seo.breadcrumbs(ctx, trail)]
    return seo.Seo(path=path, title=name, description=description, image=image, jsonld=jsonld)
