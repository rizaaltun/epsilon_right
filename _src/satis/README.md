# International book finder: /satis/

The Turkish reader catalogue is exported as a standalone React application in `satis/`. It has its own scoped assets and does not change the rights website header or homepage content. A small link is rendered in the common footer by `sitegen/shell.py`.

The public catalogue API runs on the existing Epsilon catalogue Sites Worker with its D1 request database. It accepts cross-origin catalogue requests only from the apex and www Epsilon domain. Anonymous reader IDs are pseudonymous UUIDs, hashed before storage; third-party cookies are not required. Owner identity and the server-side password remain required for demand management. The `/satis/talepler/` shortcut opens that protected management screen in a top-level page.

The maintained source contains `scripts/export-main-site.mjs`; run it with the absolute main-site checkout path to refresh the frontend, then run `python _src/build.py` and `python _src/build.py --check` here. Do not overwrite the main site's `assets/`, CNAME, or Pages settings. No backend passwords or credentials are in this repository.
