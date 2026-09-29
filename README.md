# Epsilon Publishing Group — website

Static export of the EYG rights site: 355 prerendered pages, ready to publish
with GitHub Pages (or any static host — Netlify, S3, plain nginx, etc.).

## Structure

- `index.html` — home page.
- `<section>/index.html`, `<section>/<slug>/index.html` — every other page
  (books, authors, publishers, catalogues, news, fairs & events, services,
  about us, contact), one real HTML file per URL.
- `assets/styles.css` — the site's compiled stylesheet, shared by every page.
- `assets/site.js` — the site's interactive layer (scroll hero, nav, the
  /books search & filters, book-cover lightbox), shared by every page.
- `assets/meta.json` — lightweight per-book data (title, author, category,
  language, year, cover) used client-side by the search/filter page and the
  homepage category previews.
- `assets/images/…` — every local image the site uses (team photos, fair
  photos, brand marks, news photos). Book covers are stored as responsive WebP variants in `assets/images/covers`.
  Source URLs, dimensions and byte counts are recorded in `assets/cover-manifest.json`.
- `assets/catalogues/…` — the two real Frankfurt 2026 rights catalogues
  (Adult Titles, Children's Titles), compressed to ~1MB PDFs.

All internal links and asset references are relative, so the site works
unmodified whether it is served from a domain root, a GitHub Pages project
subpath (`username.github.io/reponame/`), or opened locally.

## Publishing with GitHub Pages

1. Push the contents of this folder to a repository.
2. In the repo's Settings → Pages, set the source to the branch/folder you
   pushed (e.g. `main` / `/ (root)`).
3. GitHub Pages serves `index.html` for a directory automatically, so every
   link (`/about-us`, `/books/…`, etc.) resolves correctly once the folder
   structure above is at the repository root.

## Known gap

The Young Adult catalogue PDF was never supplied, so its "Open catalogue" /
"Download" buttons (on `/catalogues/young-adult-titles-2026` and on each
Young Adult book page) are intentionally disabled rather than pointing at a
file that does not exist. Add the real PDF at
`assets/catalogues/ya-catalogue-2026.pdf` and re-enable those two links
(remove the `aria-disabled`/`style="pointer-events:none…"` attributes) once
it is available.

## Asset maintenance

Run `python scripts/optimize_site.py` with Pillow 11.3.0, or run the
**Optimize website assets** workflow on main. The script downloads original
covers, validates the images, generates WebP variants at up to 480 and 1000
pixels wide (quality 86), and updates HTML and metadata. Failed downloads
keep their original URLs and fail the workflow visibly. The workflow commits
changes and explicitly requests a Pages build without altering the Pages
source or CNAME. It also removes only the Services link inside footers.

## Contact form

The form uses FormSubmit with recipient pelin@epsilonyayingrubu.com, native
required/email validation, whitespace validation, a honeypot and FormSubmit's
default verification step. The recipient must confirm FormSubmit's activation
email after the first submission. Deployment does not verify inbox delivery.
Do not send test submissions without the site owner's permission.
