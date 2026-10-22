"""A small Markdown subset for article bodies written in the admin panel.

Blocks (separated by blank lines): paragraphs, ``## `` / ``### `` headings,
``- `` bullet lists, ``1. `` numbered lists and ``> `` quotes.
Inline: ``**bold**``, ``*italic*`` / ``_italic_`` and ``[text](url)`` links;
links to other sites open in a new tab. A backslash escapes the next character.

The output matches the markup of the site's original articles.
"""

import re

from .html import esc

_INLINE = re.compile(
    r"\\(?P<escaped>[\\`*_\[\]()#>!-])"
    r"|\[(?P<text>(?:\\.|[^\]\\])+)\]\((?P<url>[^)\s]+)\)"
    r"|\*\*(?P<strong>.+?)\*\*"
    r"|(?<![\w*])\*(?P<em>[^*\s](?:[^*]*[^*\s])?)\*(?!\*)"
    r"|(?<![\w])_(?P<em2>[^_\s](?:[^_]*[^_\s])?)_(?![\w])"
)


def inline(text: str) -> str:
    out, pos = [], 0
    for m in _INLINE.finditer(text):
        out.append(esc(text[pos:m.start()]))
        pos = m.end()
        if m.group("escaped"):
            out.append(esc(m.group("escaped")))
        elif m.group("url"):
            url = m.group("url")
            external = ' target="_blank" rel="noopener noreferrer"' if re.match(r"https?://", url) else ""
            out.append(f'<a class="link" href="{esc(url)}"{external}>{inline(m.group("text"))}</a>')
        elif m.group("strong"):
            out.append(f"<strong>{inline(m.group('strong'))}</strong>")
        else:
            out.append(f"<em>{inline(m.group('em') or m.group('em2'))}</em>")
    out.append(esc(text[pos:]))
    return "".join(out)


def _list(lines, ordered):
    tag = "ol" if ordered else "ul"
    marker = r"\d+[.)]\s+" if ordered else r"[-*+]\s+"
    items, current = [], None
    for line in lines:
        m = re.match(marker, line)
        if m:
            if current is not None:
                items.append(current)
            current = line[m.end():]
        elif current is not None:
            current += " " + line.strip()
    if current is not None:
        items.append(current)
    return f"<{tag}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{tag}>"


def to_html(source: str) -> str:
    html = []
    for block in re.split(r"\n\s*\n", (source or "").replace("\r\n", "\n").strip()):
        lines = [l.rstrip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue
        first = lines[0]
        heading = re.match(r"(#{2,4})\s+(.*)", first)
        if heading and len(lines) == 1:
            level = len(heading.group(1))
            html.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
        elif all(re.match(r"[-*+]\s+", l) or l.startswith("  ") for l in lines) and re.match(r"[-*+]\s+", first):
            html.append(_list(lines, ordered=False))
        elif re.match(r"\d+[.)]\s+", first) and all(re.match(r"\d+[.)]\s+", l) or l.startswith("  ") for l in lines):
            html.append(_list(lines, ordered=True))
        elif all(l.startswith(">") for l in lines):
            quote = "\n\n".join(re.sub(r"^>\s?", "", l) for l in lines)
            html.append(f"<blockquote>{to_html(quote)}</blockquote>")
        else:
            html.append(f"<p>{inline(' '.join(l.strip() for l in lines))}</p>")
    return "".join(html)
