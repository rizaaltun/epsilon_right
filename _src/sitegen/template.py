"""A very small template language for page fragments.

    {{name}}                     value, HTML-escaped; dotted names look into objects
    {{name|filter|filter:arg}}   filters, see FILTERS
    {{#each list}}…{{/each}}     repeat for each item; inside, names resolve on the item
                                 first, then outward; {{@index}} (0-based), {{@odd}}, {{@first}}
    {{#if name}}…{{else}}…{{/if}}  a block shown when the value is non-empty

The page's prefix back to the site root is {{@r}}.
"""

import re

from . import markdown
from .html import esc

_TOKEN = re.compile(r"{{\s*(#each|#if|/each|/if|else)?\s*([^}|]*?)\s*((?:\|[^}|]+)*)\s*}}")


class _Raw(str):
    """A value that is already HTML and must not be escaped again."""


def _split_value(value: str):
    """'100+' -> ('', '100', '+'): prefix, number and suffix for counters."""
    m = re.fullmatch(r"(\D*?)([\d.,]+)(\D*)", str(value).strip())
    return m.groups() if m else ("", "", str(value))


FILTERS = {
    "path": lambda v, ctx, *a: ctx.lookup("@r") + str(v).lstrip("/"),                 # site path -> relative URL
    "tel": lambda v, ctx, *a: "tel:" + re.sub(r"[^\d+]", "", str(v)),                   # phone -> tel: link
    "md": lambda v, ctx, *a: _Raw(markdown.to_html(str(v))),                            # Markdown -> HTML
    "num": lambda v, ctx, *a: _split_value(v)[1].replace(",", ""),                      # '100+' -> '100'
    "prefix": lambda v, ctx, *a: _split_value(v)[0],
    "suffix": lambda v, ctx, *a: _split_value(v)[2],
    "len": lambda v, ctx, *a: str(len(v or [])),
    "plural": lambda v, ctx, one, many: f"{len(v or [])} {one if len(v or []) == 1 else many}",
}


class _Context:
    def __init__(self, frames):
        self.frames = frames

    def child(self, frame):
        return _Context([frame] + self.frames)

    def lookup(self, name):
        if name == ".":
            return self.frames[0].get(".", "") if isinstance(self.frames[0], dict) else ""
        for frame in self.frames:
            value, found = frame, True
            for part in name.split("."):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    found = False
                    break
            if found:
                return value
        return ""


def _parse(source):
    """Nested list of text pieces and (kind, name, filters, body, else_body) nodes."""
    root, stack, pos = [], [], 0
    current = root
    for m in _TOKEN.finditer(source):
        current.append(source[pos:m.start()])
        pos = m.end()
        kind, name, filters = m.group(1), m.group(2), [f for f in m.group(3).split("|") if f]
        if kind in ("#each", "#if"):
            node = [kind, name, filters, [], None]
            current.append(node)
            stack.append((node, current))
            current = node[3]
        elif kind == "else":
            node, _ = stack[-1]
            node[4] = []
            current = node[4]
        elif kind in ("/each", "/if"):
            node, parent = stack.pop()
            if node[0] != "#" + kind[1:]:
                raise ValueError(f"template: {{{{{kind}}}}} closes {{{{{node[0]} {node[1]}}}}}")
            current = parent
        else:
            current.append(("var", name, filters))
    if stack:
        raise ValueError(f"template: unclosed {{{{{stack[-1][0][0]} {stack[-1][0][1]}}}}}")
    current.append(source[pos:])
    return root


def _apply(value, filters, ctx):
    for f in filters:
        name, *args = f.split(":")
        value = FILTERS[name](value, ctx, *args)
    return value


def _render(nodes, ctx):
    out = []
    for node in nodes:
        if isinstance(node, str):
            out.append(node)
        elif node[0] == "var":
            value = _apply(ctx.lookup(node[1]), node[2], ctx)
            out.append(value if isinstance(value, _Raw) else esc(value))
        elif node[0] == "#if":
            value = _apply(ctx.lookup(node[1]), node[2], ctx)
            out.append(_render(node[3] if value else (node[4] or []), ctx))
        else:
            items = ctx.lookup(node[1]) or []
            for i, item in enumerate(items):
                frame = {"@index": i, "@odd": i % 2 == 1, "@first": i == 0}
                if isinstance(item, dict):
                    frame.update(item)
                else:
                    frame["."] = item
                out.append(_render(node[3], ctx.child(frame)))
    return "".join(out)


def render(source: str, *frames) -> str:
    """Render ``source`` with names looked up in ``frames`` (first wins)."""
    if "{{" not in source:
        return source
    return _render(_parse(source), _Context(list(frames)))
