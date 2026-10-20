"""One-off migration: the editable texts of the hand-built pages move into
content the admin panel can edit.

- _src/content/pages/<path>/texts.json   headings, paragraphs and images of a page
- _src/content/settings/stats.json       "The group in numbers" (home and About)
- _src/content/settings/contact.json     contact details and offices
- _src/content/services/<slug>.json      the five service pages

Each page fragment gets {{placeholders}} (sitegen/template.py) where the text
was. The build must still reproduce every page, which `build.py --check`
verifies. Run from the repository root:  python3 _src/tools/migrate_page_texts.py
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from html_to_markdown import convert  # noqa: E402
from sitegen.html import esc  # noqa: E402

CONTENT = ROOT / "_src/content"
PAGES = CONTENT / "pages"


class Page:
    """A fragment being turned into a template, with a cursor so repeated
    strings are matched in document order."""

    def __init__(self, path):
        self.path = path
        self.file = PAGES / path / "index.html"
        self.html = self.file.read_text(encoding="utf-8")
        self.texts = {}
        self.pos = 0

    def _replace(self, old, new, what):
        i = self.html.find(old, self.pos)
        if i < 0:
            raise ValueError(f"{self.path or 'home'}: {what} not found after {self.pos}: {old[:80]!r}")
        self.html = self.html[:i] + new + self.html[i + len(old):]
        self.pos = i + len(new)

    def text(self, key, value):
        """An element's text: >value< becomes >{{key}}<."""
        self.texts[key] = value
        self._replace(f">{esc(value)}<", f">{{{{{key}}}}}<", key)

    def attr(self, key, name, value, filt=""):
        """An attribute value, e.g. an image's alt or src."""
        self._replace(f'{name}="{value}"', f'{name}="{{{{{key}{filt}}}}}"', key)

    def image(self, key, alt_key, alt, src):
        """<img alt=… … src=…>: both become editable (src as a site path)."""
        self.texts[alt_key] = html.unescape(alt)
        self.attr(alt_key, "alt", alt)
        self.texts[key] = "/" + src.replace("../", "")
        self.attr(key, "src", src, "|path")

    def prose(self, key, opening):
        """The <p> paragraphs inside the element opened by ``opening`` become Markdown."""
        start = self.html.find(opening, self.pos)
        if start < 0:
            raise ValueError(f"{self.path}: {opening} not found")
        inner_start = start + len(opening)
        inner_end = self.html.find("</div>", inner_start)
        self.texts[key] = convert(self.html[inner_start:inner_end])
        self.html = self.html[:inner_start] + f"{{{{{key}|md}}}}" + self.html[inner_end:]
        self.pos = inner_start

    def region(self, start_marker, end_marker, replacement):
        """Replace everything between two markers (exclusive) and return the old HTML."""
        a = self.html.find(start_marker, self.pos)
        b = self.html.find(end_marker, a + len(start_marker))
        if a < 0 or b < 0:
            raise ValueError(f"{self.path}: region {start_marker[:40]!r} … {end_marker[:40]!r} not found")
        a += len(start_marker)
        old = self.html[a:b]
        self.html = self.html[:a] + replacement + self.html[b:]
        self.pos = a + len(replacement)
        return old

    def header(self):
        """The common page header: eyebrow, title and intro line."""
        m = re.search(r'<header class="border-b border-rule bg-surface py-12 md:py-18"><div class="shell"><div class="max-w-3xl">'
                      r'(?:<p class="eyebrow mb-4">(.*?)</p>)?<h1 class="text-display-lg">(.*?)</h1>'
                      r'(?:<p class="mt-5 max-w-2xl text-lg leading-relaxed text-ink-2">(.*?)</p>)?', self.html[self.pos:])
        for key, value in zip(("eyebrow", "title", "intro"), m.groups()):
            if value is not None:
                self.text(key, html.unescape(value))

    def save(self):
        self.file.write_text(self.html, encoding="utf-8")
        (self.file.parent / "texts.json").write_text(json.dumps(self.texts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def templatize(block, pairs):
    """Turn one rendered item into a template: each (literal, placeholder) in order."""
    pos = 0
    for literal, placeholder in pairs:
        i = block.find(literal, pos)
        if i < 0:
            raise ValueError(f"templatize: {literal[:60]!r} not found")
        block = block[:i] + placeholder + block[i + len(literal):]
        pos = i + len(placeholder)
    return block


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


STAT = re.compile(r'<div class="flex flex-col[^"]*"><dt class="[^"]*">(.*?)</dt><dd class="order-1[^"]*">(?:<span[^>]*>)?(.*?)(?:</span>)?</dd>'
                  r'(?:<dd class="order-3[^"]*">(.*?)</dd>)?</div>')


def stats_template(page, dl_open):
    """Replace the <dl> items with an {{#each}} built from the first item."""
    items_html = page.region(dl_open, "</dl>", "@@STATS@@")
    first = re.match(r'<div class="flex flex-col.*?</div>', items_html).group(0)
    label, value, note = STAT.match(first).groups()
    pairs = [(f">{label}<", ">{{label}}<")]
    if "data-countup" in first:
        pairs.append(('data-countup="100" data-prefix="" data-suffix="+">100+<',
                      'data-countup="{{value|num}}" data-prefix="{{value|prefix}}" data-suffix="{{value|suffix}}">{{value}}<'))
    else:
        pairs.append((f">{value}<", ">{{value}}<"))
    pairs.append((f'<dd class="order-3', '{{#if note}}<dd class="order-3'))
    pairs.append((f">{note}</dd>", ">{{note}}</dd>{{/if}}"))
    item = templatize(first, pairs)
    page.html = page.html.replace("@@STATS@@", "{{#each stats.items}}" + item + "{{/each}}")
    return [{"label": html.unescape(l), "value": html.unescape(v), **({"note": html.unescape(n)} if n else {})}
            for l, v, n in STAT.findall(items_html)]


def home():
    p = Page("")
    p.text("h1", "Epsilon Publishing Group — We connect stories with the world.")
    p.text("hero_title", "Epsilon Publishing Group")
    p.text("hero_text", "We connect stories with the world. Discover original titles, explore global rights opportunities, and build lasting partnerships.")
    p.text("hero_button", "Discover more")
    p.text("intro_eyebrow", "Epsilon Publishing Group")
    p.text("intro_title", "Turkish stories, travelling the world")
    p.prose("intro_body", '<div class="prose-editorial mt-6">')
    p.text("intro_link", "About the group")
    p.image("intro_image", "intro_image_alt", "Epsilon Publishing Group team presenting titles at a book fair stand",
            "assets/images/demo/home-turkish-stories.jpg")
    p.text("catalogue_eyebrow", "Browse")
    p.text("catalogue_title", "The catalogue")
    for key, title in (("fiction_title", "Fiction highlights"), ("non_fiction_title", "Non-fiction highlights"),
                       ("younger_title", "For younger readers")):
        p.text(key, title)
        p.attr(key, "aria-label", title)
    p.text("news_eyebrow", "News")
    p.text("news_title", "From the desk")
    p.text("stats_title", "The group in numbers")
    stats = stats_template(p, '<dl class="grid grid-cols-2 gap-x-8 gap-y-10 md:grid-cols-4">')
    p.text("cta_eyebrow", "Rights enquiries")
    p.text("cta_title", "Tell us which territory you publish in")
    p.prose("cta_body", '<div class="prose-editorial mt-4">')
    p.text("cta_button", "Contact the rights team")
    p.save()
    write_json(CONTENT / "settings/stats.json", {"items": stats})


BRAND = re.compile(r'<div class="grid gap-8 md:grid-cols-2 md:items-center md:gap-14"><div class="(?:md:order-2)?"><p class="eyebrow mb-3">(.*?)</p>'
                   r'<h2 class="text-display-sm text-balance">(.*?)</h2><div class="prose-editorial mt-5">(.*?)</div></div>'
                   r'<div class="relative overflow-hidden bg-paper-3 rounded-lg" style="aspect-ratio:4/3"><img alt="([^"]*)"[^>]*src="([^"]+)"/></div></div>')


def about():
    p = Page("about-us")
    p.header()
    p.image("hero_image", "hero_image_alt", "The Epsilon Publishing Group team at work in the Istanbul office",
            "../assets/images/demo/about-group-intro.jpg")
    lead = re.search(r'<p class="font-display text-xl leading-relaxed text-ink md:text-2xl">(.*?)</p>', p.html).group(1)
    p.text("lead", html.unescape(lead))
    p.prose("body", '<div class="prose-editorial mt-8">')

    start = '<div class="grid gap-16 md:gap-24">'
    blocks = p.region(start, '<div class="grid gap-8"><div class="">', "@@BRANDS@@")
    brands = [{"eyebrow": html.unescape(e), "quote": html.unescape(q), "body": convert(b),
               "image": "/" + src.replace("../", ""), "image_alt": html.unescape(alt)}
              for e, q, b, alt, src in BRAND.findall(blocks)]
    first = BRAND.match(blocks).group(0)
    e, q, b, alt, src = BRAND.match(first).groups()
    item = templatize(first, [('<div class="">', '<div class="{{#if @odd}}md:order-2{{/if}}">'), (f">{e}<", ">{{eyebrow}}<"),
                              (f">{q}<", ">{{quote}}<"), (b, "{{body|md}}"), (f'alt="{alt}"', 'alt="{{image_alt}}"'),
                              (f'src="{src}"', 'src="{{image|path}}"')])
    assert "".join(BRAND.findall(blocks) and [m.group(0) for m in BRAND.finditer(blocks)]) == blocks, "unexpected brand markup"
    p.html = p.html.replace("@@BRANDS@@", "{{#each brands}}" + item + "{{/each}}")
    p.texts["brands"] = brands

    p.text("next_eyebrow", "The Next Chapter")
    p.text("next_title", "Where we are heading")
    p.prose("next_body", '<div class="prose-editorial mt-5">')
    stats_template(p, '<dl class="grid grid-cols-2 gap-x-8 gap-y-10 md:grid-cols-4">')
    p.text("team_title", "The team")
    p.text("team_intro", "Grouped by department. Open a department to see who to contact.")

    team = p.region('<div class="divide-y divide-rule border-y border-rule">', "</div></div></div></section>", "@@TEAM@@")
    dept = re.match(r"<div><h3><button.*?</ul></div></div></div>", team, re.S).group(0)
    assert dept == team, "expected one department"
    name = re.search(r'<span class="font-display text-xl">(.*?)</span>', dept).group(1)
    people_html = re.search(r'<ul class="grid gap-x-8 gap-y-9 sm:grid-cols-2 xl:grid-cols-3">(.*?)</ul>', dept, re.S).group(1)
    person_re = re.compile(r'<li><article class="flex gap-4">.*?<img alt="([^"]*)"[^>]*src="([^"]+)"/></div><div class="min-w-0"><h3[^>]*>(.*?)</h3>'
                           r'<p class="mt-0.5 text-sm text-accent">(.*?)</p><div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs"><a href="mailto:([^"]+)" class="link">.*?</a></div></div></article></li>', re.S)
    people = [{"name": html.unescape(n), "role": html.unescape(role), "email": email, "photo": "/" + src.replace("../", "")}
              for _alt, src, n, role, email in person_re.findall(people_html)]
    first_person = person_re.match(people_html).group(0)
    alt, src, n, role, email = person_re.match(first_person).groups()
    person_tpl = templatize(first_person, [('<img ', '{{#if photo}}<img '), (f'alt="{alt}"', 'alt="{{name}}"'),
                                           (f'src="{src}"/>', 'src="{{photo|path}}"/>{{/if}}'), (f">{n}<", ">{{name}}<"),
                                           (f">{role}<", ">{{role}}<"), ('<div class="mt-2', '{{#if email}}<div class="mt-2'),
                                           (f'mailto:{email}', 'mailto:{{email}}'),
                                           (f">{email}</a></div>", ">{{email}}</a></div>{{/if}}")])
    dept_tpl = dept.replace(people_html, "{{#each people}}" + person_tpl + "{{/each}}")
    dept_tpl = dept_tpl.replace(f"-{name}-", "-{{name}}-").replace(f">{name}<", ">{{name}}<")
    dept_tpl = dept_tpl.replace(">2 people<", ">{{people|plural:person:people}}<")
    p.html = p.html.replace("@@TEAM@@", "{{#each departments}}" + dept_tpl + "{{/each}}")
    p.texts["departments"] = [{"name": html.unescape(name), "people": people}]
    p.save()


def contact():
    p = Page("contact")
    p.header()
    p.text("form_title", "Send us a message")
    p.text("details_title", "Contact details")
    details = p.region('<dl class="divide-y divide-rule border-y border-rule text-sm mt-6">', "</dl>", "@@DETAILS@@")
    row = '<div class="grid grid-cols-[minmax(7rem,9rem)_1fr] gap-4 py-3"><dt class="text-ink-3">{label}</dt><dd class="text-ink">{value}</dd></div>'
    tpl = (
        "{{#if contact.email}}" + row.format(label="Email", value='<a href="mailto:{{contact.email}}" class="link">{{contact.email}}</a>') + "{{/if}}"
        "{{#if contact.rights_email}}" + row.format(label="Rights enquiries", value='<a href="mailto:{{contact.rights_email}}" class="link">{{contact.rights_email}}</a>') + "{{/if}}"
        "{{#if contact.phone}}" + row.format(label="Phone", value='<a href="{{contact.phone|tel}}" class="link">{{contact.phone}}</a>') + "{{/if}}"
        "{{#if contact.address}}" + row.format(label="Address", value='<address class="not-italic">{{contact.address}}</address>') + "{{/if}}"
    )
    p.html = p.html.replace("@@DETAILS@@", tpl)
    found = dict(re.findall(r'<dt class="text-ink-3">(.*?)</dt><dd class="text-ink">(.*?)</dd>', details))
    strip = lambda v: html.unescape(re.sub(r"<[^>]+>", "", v))
    data = {"email": strip(found["Email"]), "rights_email": strip(found["Rights enquiries"]),
            "phone": strip(found["Phone"]), "address": strip(found["Address"])}

    p.text("office_title", "Head office")
    office_html = p.region('lg:gap-14">', "</div></div></div></section>", "@@OFFICES@@")
    m = re.fullmatch(r'<article class="card flex h-full w-full flex-col p-6"><h3 class="font-display text-lg leading-snug">(.*?)</h3>'
                     r'<p class="mt-1 text-\[0.8125rem\] text-ink-3">(.*?)</p><address class="mt-3 text-sm leading-relaxed text-ink-2 not-italic">(.*?)</address>'
                     r'<div class="mt-3 flex flex-col gap-1 text-sm"><a href="tel:[^"]+" class="link">(.*?)</a></div>'
                     r'<p class="mt-3 text-\[0.8125rem\] text-ink-3">(.*?)</p><a href="([^"]+)" class="link-arrow mt-auto pt-5 text-sm" target="_blank" rel="noopener noreferrer">View on map</a></article>',
                     office_html, re.S)
    name, city, address, phone, hours, _placeholder_map = m.groups()
    p.html = p.html.replace("@@OFFICES@@", (
        '{{#each contact.offices}}<article class="card flex h-full w-full flex-col p-6"><h3 class="font-display text-lg leading-snug">{{name}}</h3>'
        '{{#if city}}<p class="mt-1 text-[0.8125rem] text-ink-3">{{city}}</p>{{/if}}{{#if address}}<address class="mt-3 text-sm leading-relaxed text-ink-2 not-italic">{{address}}</address>{{/if}}'
        '{{#if phone}}<div class="mt-3 flex flex-col gap-1 text-sm"><a href="{{phone|tel}}" class="link">{{phone}}</a></div>{{/if}}'
        '{{#if hours}}<p class="mt-3 text-[0.8125rem] text-ink-3">{{hours}}</p>{{/if}}{{#if map_url}}<a href="{{map_url}}" class="link-arrow mt-auto pt-5 text-sm" target="_blank" rel="noopener noreferrer">View on map</a>{{/if}}</article>{{/each}}'))
    plain_address = html.unescape(address)
    data["offices"] = [{
        "name": html.unescape(name), "city": html.unescape(city), "address": plain_address,
        "phone": html.unescape(phone), "hours": html.unescape(hours),
        # The export linked to https://maps.example.com (a placeholder).
        "map_url": "https://www.google.com/maps/search/?api=1&query=" + "+".join(plain_address.split("\n")[0].replace(",", "").split()),
    }]
    p.save()
    write_json(CONTENT / "settings/contact.json", data)


SERVICE_ORDER = ["copyrights", "licensing", "translation", "international-cultural-organisations", "publishing-grants"]


def services():
    index = Page("services")
    index.header()
    cards = index.region('<ul class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">', "</ul>", "<!--@service-cards-->")
    card_images = dict(re.findall(r'href="\.\./services/([^/]+)/"><div[^>]*><img alt="[^"]*"[^>]*src="\.\./([^"]+)"', cards))
    index.save()
    for order, slug in enumerate(SERVICE_ORDER, start=1):
        src = (PAGES / f"services/{slug}/index.html").read_text(encoding="utf-8")
        hero = re.search(r'style="aspect-ratio:21/9"><img alt="([^"]*)"[^>]*src="\.\./\.\./([^"]+)"', src)
        title = html.unescape(re.search(r'<h1 class="text-display-lg">(.*?)</h1>', src).group(1))
        item = {
            "title": title,
            "summary": html.unescape(re.search(r'<p class="mt-5 max-w-2xl text-lg leading-relaxed text-ink-2">(.*?)</p>', src).group(1)),
            "body": convert(re.search(r'<div class="prose-editorial">(.*?)</div>', src).group(1)),
            "covers": [html.unescape(c) for c in re.findall(r"</svg><span>(.*?)</span></li>", src)],
            "image": "/" + card_images[slug],
            "hero_image": "/" + hero.group(2),
            "order": order,
        }
        if html.unescape(hero.group(1)) != title:
            item["image_alt"] = html.unescape(hero.group(1))
        write_json(CONTENT / f"services/{slug}.json", item)
        shutil.rmtree(PAGES / f"services/{slug}")


def headers():
    for path in ("books", "authors", "publishers", "news", "fairs-events", "catalogues", "representations"):
        p = Page(path)
        p.header()
        p.save()


def main():
    if (CONTENT / "settings/stats.json").exists() and "--force" not in sys.argv:
        sys.exit("page texts were already migrated; pass --force to run again")
    home()
    about()
    contact()
    services()
    headers()
    print("migrated page texts, stats, contact details and services")


if __name__ == "__main__":
    sys.exit(main())
