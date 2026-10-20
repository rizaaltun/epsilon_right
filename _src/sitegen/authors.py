"""Author pages: /authors/<slug>/."""

from . import seo, shell
from .books import paragraphs
from .components import book_card, breadcrumb, section_heading
from .html import esc, prefix_for


def initials(name: str) -> str:
    words = name.split()
    return "".join(w[0] for w in words[:2]).upper()


def render(ctx, slug: str) -> tuple:
    author = ctx.authors[slug]
    path = f"authors/{slug}/"
    r = prefix_for(path)
    bio = f'<div class="prose-editorial">{paragraphs(author["bio"])}</div>' if author.get("bio") else ""
    titles = ctx.books_by_author(slug)
    titles_section = ""
    if titles:
        cards = "".join(f"<li>{book_card(ctx, r, s, b)}</li>" for s, b in titles)
        titles_section = (
            '<section class="py-14 md:py-20 ground-paper"><div><div class="shell">'
            + section_heading("Titles")
            + '<ul class="grid grid-cols-2 gap-x-5 gap-y-9 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">'
            f"{cards}</ul></div></div></section>"
        )
    main = (
        '<main id="main" class="flex-1">'
        + breadcrumb(r, [("", "Home"), ("authors/", "Authors")], author["name"])
        + '<section class="py-14 md:py-20 pt-8 md:pt-10"><div><div class="shell"><div class="grid gap-8 '
        'md:grid-cols-[minmax(0,16rem)_minmax(0,1fr)] md:gap-12 lg:gap-16"><div class="flex items-center '
        'justify-center bg-paper-3 text-ink-3 rounded-md" style="aspect-ratio:4/5" aria-hidden="false"><span '
        f'class="font-display text-4xl text-ink-3">{esc(initials(author["name"]))}</span></div><div class="min-w-0">'
        f'<h1 class="text-display-lg">{esc(author["name"])}</h1></div></div><div class="mt-14 max-w-3xl">{bio}</div>'
        "</div></div></section>"
        + titles_section
        + "<!--$--><!--/$--></main>"
    )
    names = [b["title"] for _, b in titles]
    listed = ", ".join(names[:3]) + ("…" if len(names) > 3 else "")
    fallback = (f'{author["name"]} — author represented by {ctx.settings["site_name"]}'
                + (f'. Titles: {listed}.' if names else "."))
    person = {"@type": "Person", "name": author["name"], "url": seo.url(ctx, path)}
    if author.get("bio"):
        person["description"] = seo.clip(author["bio"], 500)
    profile = {"@type": "ProfilePage", "url": seo.url(ctx, path), "mainEntity": person}
    meta = seo.Seo(path=path, title=author["name"], description=seo.describe(author, author.get("bio"), fallback),
                   type="profile", jsonld=[profile, seo.breadcrumbs(ctx, [("Home", ""), ("Authors", "authors/"),
                                                                            (author["name"], path)])])
    return path, shell.page(r, path, ctx.settings, seo.title_html(ctx, author, author["name"]), main,
                            seo_html=seo.head_tags(ctx, meta))
