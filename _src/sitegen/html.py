"""Small HTML helpers shared by every renderer.

Escaping mirrors React's server renderer, which produced the original pages:
text and attribute values escape & < > " and ' (the apostrophe as &#x27;).
"""

_ESCAPES = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;"}


def esc(value) -> str:
    """Escape text or an attribute value exactly like the original site."""
    s = str(value)
    if not any(c in s for c in _ESCAPES):
        return s
    return "".join(_ESCAPES.get(c, c) for c in s)


def esc_title(value) -> str:
    """Escape a <title>; the original titles keep quotes and apostrophes raw."""
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def prefix_for(path: str) -> str:
    """Relative prefix from a page directory back to the site root.

    ``path`` is the page's URL path without leading slash, e.g. ``""`` for the
    home page, ``"books/"`` or ``"books/eflatun-koza/"``.
    """
    depth = path.strip("/").count("/") + 1 if path.strip("/") else 0
    return "../" * depth


def home_href(r: str) -> str:
    """Link to the home page; the root page itself links to ``.``."""
    return r or "."
