# International catalogue — UI and UX revision

## Primary task and design rationale

A reader arrives with a book, author or topic in mind and needs a relevant retailer in their shopping destination. The first version devoted too much space to a marketing hero, exposed four filters before search, and gave country selection the weight of a secondary form field. The page now prioritizes destination → search → local retailer. This is a task-based heuristic review and scenario testing, not research with recruited users.

| Observed friction | Change | Reason |
| --- | --- | --- |
| Large hero displaced the task | Compact introduction; no decorative shelf on narrow screens | Destination and search appear sooner |
| Timezone inferred country without network evidence | Same-origin edge country lookup, then device fallback | Prefer an approximate connection country to a language preference |
| Destination was a plain dropdown | Persistent location strip with region + country and explicit Change action | Communicate the current context before a retailer click |
| Region-only labelling could imply delivery across a whole continent | Europe · Finland, with Adlibris FI primary; other European shops secondary | Preserve exact local ranking while offering regional exploration |
| Filters competed with search | Search first, optional Filters panel with active count | Support simple search and advanced browsing without initial clutter |
| 19-store modal ignored the visitor context | Local shop first, same-region alternatives next, all destinations in a disclosure | Reduce decisions while keeping the full network accessible |
| API-disabled AI actions led to a dead end | Hide adviser/analysis actions until the endpoint is configured | Keep only useful primary actions |
| ISBN and origin labels added card clutter | ISBN moves to details; origin remains available as a filter | Emphasize title, author, retailer |
| Retailer test utility appeared in shopping UI | Remove the barcode test form from the reader flow | Keep implementation checks out of the product experience |

## Destination rules

1. A valid explicit link destination wins, so review/demo URLs are deterministic.
2. A saved deliberate selection wins over a new connection estimate: a reader may be shopping for someone abroad.
3. Otherwise query `/api/location` using same-origin, no-store HTTP. The edge handler uses `request.cf.country` and `request.cf.continent`, never visitor-supplied query parameters or CF-IPCountry headers.
4. Only country + continent + source are returned. No IP address, city, coordinates, street address or GPS request is exposed or stored by this module.
5. If the edge country is not in the retailer list but its region is supported (Spain → Europe), show that fact and regional exploration, without presenting another country's store as local. Japan is not automatically labelled Middle East.
6. If network lookup fails or times out, use a clearly labelled device suggestion. If neither works, ask the reader to choose; do not invent a destination.
7. A late network response cannot overwrite a manual choice. “Use my approximate country” clears the saved override and retries detection.
8. Automatic estimates are not persisted as a permanent preference or forced into share URLs.

Network location is approximate; VPNs/proxies may change it. The algorithm is not an address detector. Retailer discovery is not a live inventory service: every CTA opens an ISBN search. Stock and cross-border delivery need retailer confirmation.

## Implementation / deployment

- `assets/international/market.mjs` owns region grouping and pure ranking/precedence rules.
- `integration/catalog-location/location.mjs` is the coarse Cloudflare country endpoint.
- The separate review Site now includes an edge handler plus the catalogue assets, so `/api/location` is available alongside the UI.
- The main GitHub Pages site remains unchanged. To activate network country lookup there, host the endpoint on an edge route or separate approved origin and set `catalog_location_endpoint` in site settings. For a separate origin configure `ALLOWED_ORIGINS` to the exact live site origin. Without this endpoint the UI clearly falls back to device settings.
- The review site's build embeds its static assets into a self-contained Worker. Source images on the main repository remain untouched; the review copy uses smaller book images.

## Scenario checks

Automated: 10 tests cover the original catalogue/search checks plus Finland vs US device settings, saved/shared destination priority, region scope, unknown/sentinel countries, Japan fallback, and coarse endpoint privacy/header spoof protection. Main-site build check still matches all 367 existing pages.

Desktop browser: Finland → `kurk mantlu` → Kürk Mantolu Madonna → Adlibris FI ISBN link; modal's first group is Europe · Finland; selecting Europe removes country-specific primary CTAs; deliberate selection updates the location strip. A 390px layout and keyboard close/focus behavior are checked before publication. No Finland-based human session, retailer stock feed or physical mobile device was tested.

Cloudflare request metadata reference: https://developers.cloudflare.com/workers/runtime-apis/request/ .
