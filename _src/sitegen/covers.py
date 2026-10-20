"""Book cover images.

A book's ``cover`` is a site path. Covers from the original export already
point at their largest WebP variant (``/assets/images/covers/<stem>-<width>.webp``)
and every width on disk goes into the ``srcset``.

A cover uploaded through the admin panel is any other image. The build turns
it into the same 480px / 1000px WebP variants that scripts/optimize_site.py
made for the exported covers, named after a hash of the file's bytes. That
needs Pillow, which the CI build installs; without it (e.g. a local preview)
the uploaded file is shown as it is.
"""

import hashlib
import re
import sys
from functools import lru_cache
from pathlib import Path

COVERS_DIR = "assets/images/covers"
VARIANT = re.compile(r"(.+)-(\d+)\.webp")
WIDTHS = (480, 1000)
_warned = set()


def site_path(cover: str) -> str:
    """Cover path relative to the site root, without a leading slash."""
    return cover.lstrip("/")


@lru_cache(maxsize=None)
def _variants_on_disk(root: str) -> dict:
    variants = {}
    for path in Path(root, COVERS_DIR).glob("*.webp"):
        match = VARIANT.fullmatch(path.name)
        if match:
            variants.setdefault(match.group(1), []).append(int(match.group(2)))
    return {stem: sorted(widths) for stem, widths in variants.items()}


def _is_variant(rel: str) -> bool:
    folder, _, name = rel.rpartition("/")
    return folder == COVERS_DIR and bool(VARIANT.fullmatch(name))


def _pillow():
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return None
    return Image, ImageOps


@lru_cache(maxsize=None)
def make_variants(root: str, rel: str, write: bool) -> list:
    """Variants [(path, width)] for an uploaded cover, creating them if ``write``.

    Returns [] when Pillow is missing, so the caller can fall back to the upload.
    """
    pil = _pillow()
    if pil is None:
        if rel not in _warned:
            _warned.add(rel)
            print(f"warning: Pillow is not installed; {rel} is used without resized variants", file=sys.stderr)
        return []
    Image, ImageOps = pil
    source = Path(root, rel)
    stem = hashlib.sha256(source.read_bytes()).hexdigest()[:20]
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
    width, height = image.size
    out = []
    for target in sorted({min(w, width) for w in WIDTHS}):
        dest = Path(root, COVERS_DIR, f"{stem}-{target}.webp")
        if write and not dest.exists():
            resized = image.copy()
            resized.thumbnail((target, round(height * target / width)), Image.Resampling.LANCZOS)
            dest.parent.mkdir(parents=True, exist_ok=True)
            resized.save(dest, "WEBP", quality=86, method=6)
        out.append((f"{COVERS_DIR}/{stem}-{target}.webp", target))
    return out


def resolve(ctx, cover: str):
    """(src, [(path, width)]) relative to the site root; variants may be []."""
    rel = site_path(cover)
    if _is_variant(rel):
        folder, _, name = rel.rpartition("/")
        stem = VARIANT.fullmatch(name).group(1)
        widths = _variants_on_disk(ctx.root).get(stem)
        if not widths:
            raise FileNotFoundError(f"no WebP variants on disk for cover {cover}")
        variants = [(f"{folder}/{stem}-{w}.webp", w) for w in widths]
        return variants[-1][0], variants
    if not Path(ctx.root, rel).is_file():
        raise FileNotFoundError(f"cover image not found: {cover}")
    variants = make_variants(ctx.root, rel, ctx.write)
    return (variants[-1][0] if variants else rel), variants
