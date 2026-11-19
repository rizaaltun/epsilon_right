# Draft legal pages (not on the site)

`privacy-policy/` and `terms/` are draft Privacy Policy and Terms of Use pages, written 19 November 2026 for
review by Rıza and a lawyer (review copy: https://claude.ai/artifact/QjjCWsJPjVDgwBw8C8dxpZ). The build only reads
`_src/content/pages/`, so nothing here is published.

To put them on the site:

1. Move both folders to `_src/content/pages/` (update `body` and `updated` in each `texts.json` first).
2. Paste `panel-fields.yml` into `admin/config.yml` so they can be edited in the panel.
3. Build. The footer's "Privacy policy" and "Terms of use" links appear by themselves once the pages exist
   (`sitegen/content.py`, `_has_privacy` / `_has_terms`).
