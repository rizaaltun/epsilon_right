# International retail catalogue — review handoff

Status: prepared on `feature/international-catalog-preview`; not merged, enabled or deployed.

## Review

From the repository root, run `python scripts/build_international_catalog.py` and serve the repository with a static HTTP server. Open `/preview/international-catalog/`. Do not open as file:// because the data is fetched as JSON.

The page reuses the existing shell, compiled CSS, fonts, buttons, colours and local logo assets. Additional CSS is scoped under `.ic`. No production pages, CNAME, main navigation, sitemap or workflow are changed by the preview builder. The sole shared browser fix makes the static-export control-disabling routine skip `[data-live-controls]` modules.

## Catalogue audit

- All 430 supplied rows, unique ISBNs and ISBN-13 checksums pass.
- 10 publishers; 156 Turkish-author entries and 274 translated-author entries.
- 178 unique **author credit strings**, including multi-author strings, collective credits and one suspicious `Childhood Narcissism` author value. They are preserved from the handoff, not verified as 178 individual people. Source spelling and truncated titles are preserved pending editorial correction.
- **14 countries, 19 retailers** in the supplied list, despite the handoff's “13 countries” claim.
- 73 covers matched by ISBN to the existing local cover manifest. Remaining covers use clearly labelled typographic placeholders, not fabricated cover art. No external image requests are needed.
- Retailer templates are supplied ISBN/keyword **search** URLs; no live stock, direct product match, Gardners feed or distribution agreement has been verified. Retailer templates still need live checks before release.
- Device timezone/language gives a suggestion, not verified physical location. Unsupported countries (including Türkiye) default to all destinations. Manual choice persists locally and is also shareable in the URL.

## Activation after design approval

1. Review this branch and merge only when ready for release. GitHub Pages publishes main, so merging source can trigger the existing site build workflow.
2. Set `international_catalog_enabled: true` in `_src/content/settings/site.json`.
3. Run `python _src/build.py`. The optional module generates `/international-catalog/`, includes it in the generated sitemap, and adds desktop/mobile/footer links. The preview banner and noindex are omitted from the production renderer.
4. Inspect the generated diff and run project build checks and the catalogue tests. Commit generated output following the repository's existing workflow, then deploy using its existing Pages process.
5. To disable navigation and generation, set the flag false. To retract an already published route, remove its generated `international-catalog/index.html` separately: the existing generator does not remove obsolete files.

The feature flag is absent (false) in the current settings. No activation steps above have been executed.

## Optional Gemini service

GitHub Pages cannot hold a secret or run the API proxy. `catalog-advisor/worker.mjs` is a separate Cloudflare Worker adapter. It validates request sizes, origins, modes and ISBNs, requires a platform rate limiter, sets a model timeout, and filters model recommendation ISBNs against the catalogue. Its tests mock Google; no billable calls were made.

Before enabling AI:

1. Copy `wrangler.example.jsonc` to your deployment configuration outside static output. Use the documented Cloudflare rate-limit binding and choose a suitable namespace and account budget. The sample binding shape was checked against https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/ . Verify account configuration before deployment.
2. Configure `GEMINI_API_KEY` as a secret and `GEMINI_MODEL` as an environment variable with a model available to your account. The handoff's `gemini-3-flash-preview` is not hard-coded or assumed available.
3. Set `ALLOWED_ORIGINS` to the exact approved site origins; add an exact preview origin only for testing. No wildcard CORS.
4. Deploy the separate Worker and verify a real request, timeout and quota behavior with the chosen account.
5. Set `catalog_advisor_endpoint` in site settings to the deployed HTTPS `/catalog-advisor` endpoint, then rebuild. Preview can use `window.EPSILON_CATALOG_CONFIG = {advisorEndpoint: 'https://…/catalog-advisor'}` before its module loads.

Until then the UI explains that AI is unavailable, while catalogue and retailer features work. The AI key is never included in browser scripts. Title/author metadata alone cannot establish plot, themes, age suitability or clinical benefits. The adviser is instructed to acknowledge uncertainty. Editorially verified summaries would improve accuracy.

API reference used: https://ai.google.dev/api/generate-content and https://ai.google.dev/gemini-api/docs/generate-content/structured-output .

## Validation

`node --test tests/international-catalog.test.mjs` covers counts, ISBN checksums, sample typo searches, routing, URL encoding, proxy input/configuration/rate-limit guards, upstream failure handling, and output ISBN allowlisting.

Browser QA: desktop rendering; `kurk mantlu` → Kürk Mantolu Madonna; Germany → Thalia and Dussmann; detail modal has 19 retailer links; Masalperest + Turkish authors → 27 titles; corresponding author-credit directory → 8 entries; Germany bookshop directory → 2 shops; unconfigured adviser state. A 390px iframe layout was checked with no horizontal body overflow; this is not a physical mobile-device session. Live retailer stock/API calls were not tested.
