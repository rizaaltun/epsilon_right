"""One-off migration: one JSON content file per exported author page.

Run from the repository root:  python3 _src/tools/migrate_authors.py
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_src"))
from sitegen.content import slugify  # noqa: E402

OUT = ROOT / "_src/content/authors"


def refuse_to_overwrite(folder: Path):
    """These migrations ran once; content is edited by hand or in the admin panel
    from then on, so re-running would silently discard those edits."""
    if folder.exists() and any(folder.iterdir()) and "--force" not in sys.argv:
        sys.exit(f"{folder.relative_to(ROOT)} already has content; pass --force to overwrite it")


def main():
    refuse_to_overwrite(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    pages = sorted((ROOT / "authors").glob("*/index.html"))
    for page in pages:
        slug = page.parent.name
        source = page.read_text(encoding="utf-8")
        name = html.unescape(re.search(r'<h1 class="text-display-lg">(.*?)</h1>', source).group(1))
        assert slugify(name) == slug, (slug, name)
        assert '<div class="mt-14 max-w-3xl"></div>' in source, f"{slug}: author page has a bio block"
        author = {"name": name, "bio": "", "photo": "", "country": "", "featured": False}
        (OUT / f"{slug}.json").write_text(json.dumps(author, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(pages)} authors to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
