"""Optional international retail module, enabled only by site settings."""
import json
from pathlib import Path
from . import shell

def render(root, settings, preview=False):
    root = Path(root)
    prefix = '../../' if preview else '../'
    main = (root / '_src/international/page.html').read_text()
    if not preview:
        start = main.index('  <div class="ic-review">')
        end = main.index('</div></div>', start) + len('</div></div>')
        main = main[:start] + main[end:]
    endpoint = settings.get('catalog_advisor_endpoint', '')
    config = json.dumps({'advisorEndpoint': endpoint, 'locationEndpoint': settings.get('catalog_location_endpoint', '')}).replace('<', '\\u003c')
    meta = '<meta name="robots" content="noindex,nofollow">' if preview else '<link rel="canonical" href="https://epsilonpublishinggroup.com/international-catalog/">'
    return shell.page(prefix, 'international-catalog/', settings,
        'International Bookshops — Epsilon Publishing Group', main,
        head_extra=meta+'<meta name="description" content="Find Turkish-language books at international bookshops."><link rel="stylesheet" href="~/assets/international/catalog.css">',
        tail_extra='<script>window.EPSILON_CATALOG_CONFIG='+config+';</script><script type="module" src="~/assets/international/catalog.mjs"></script>')

def outputs(root, settings):
    if not settings.get('international_catalog_enabled', False):
        return {}
    return {
        'international-catalog/index.html': render(root, settings),
        'assets/international/books.json': (Path(root) / '_src/international/books.json').read_text(),
    }
