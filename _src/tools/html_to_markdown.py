"""Convert the simple prose HTML of the exported articles to Markdown
(the inverse of sitegen.markdown for <p>, <strong>, <em> and <a class="link">)."""
import html
import re


def _md_escape(text: str) -> str:
    return re.sub(r"([\\`*_\[\]])", r"\\\1", text)


def _inline(fragment: str) -> str:
    def link(m):
        return f"[{_inline(m.group(2))}]({html.unescape(m.group(1))})"
    s = re.sub(r'<a class="link" href="([^"]+)"(?: target="_blank" rel="noopener noreferrer")?>(.*?)</a>', link, fragment)
    s = re.sub(r"<strong>(.*?)</strong>", lambda m: f"**{m.group(1)}**", s)
    s = re.sub(r"<em>(.*?)</em>", lambda m: f"*{m.group(1)}*", s)
    if re.search(r"<(?!/?(?:strong|em)\b)[a-z]", s):
        raise ValueError(f"unsupported markup: {fragment[:120]}")
    # unescape entities, but keep Markdown we just wrote intact
    parts = re.split(r"(\[[^\]]*\]\([^)]*\)|\*\*|\*)", s)
    return "".join(p if re.fullmatch(r"\[[^\]]*\]\([^)]*\)|\*\*|\*", p or "") else _md_escape(html.unescape(p)) for p in parts)


def convert(prose_html: str) -> str:
    paragraphs = re.findall(r"<p>(.*?)</p>", prose_html, re.S)
    if "".join(f"<p>{p}</p>" for p in paragraphs) != prose_html:
        raise ValueError("prose contains blocks other than <p>")
    return "\n\n".join(_inline(p) for p in paragraphs)
