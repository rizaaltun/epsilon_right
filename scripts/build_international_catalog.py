"""Build the isolated review page. Does not change navigation or publish anything."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '_src'))
from sitegen import shell, international_catalog


def build():
    folder = ROOT / 'preview/international-catalog'
    folder.mkdir(parents=True, exist_ok=True)
    books = json.loads((ROOT / '_src/international/books.json').read_text())
    (ROOT / 'assets/international/books.json').write_text(json.dumps(books, ensure_ascii=False, separators=(',', ':'))+'\n')
    settings = json.loads((ROOT / '_src/content/settings/site.json').read_text())
    page = international_catalog.render(ROOT, settings, preview=True)
    # No analytics during internal review.
    page = page.replace(shell.CF_ANALYTICS, '')
    (folder / 'index.html').write_text(page)
    print(f'Built {folder.relative_to(ROOT)}/index.html — {len(books)} books')

if __name__ == '__main__':
    build()
