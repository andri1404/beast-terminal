# Programmatic Local SEO — Static Site Pattern

For sites hosted on Vercel/Netlify/GitHub Pages (hand-written static HTML, NO CMS), the ranking play is **one landing page per geographic area**, not bulk blog posts. Each area page targets the query `"<service> <area>"` and carries full on-page SEO. This is how local-service sites (jasa tebas rumput, kontraktor, etc.) dominate Google local search.

## Step 0 — Detect static vs CMS (do this FIRST)

```bash
curl -sIL "https://site" | grep -iE "server:|x-powered-by:"
```
- `server: Vercel` / `Netlify` + body is hand-written `<html>` (not `wp-content/`, no `/wp-json/`) → static. Use this pattern.
- `x-powered-by: PHP` / has `/wp-json/wp/v2/` → WordPress. Use `csv2post.py` instead.

Telltale static fingerprint: `<link rel="canonical">`, inline `<script type="application/ld+json">`, Tailwind via `cdn.tailwindcss.com`, sections with `#anchors` only (single page).

## Area page anatomy (each of the 42 pages must have ALL)

1. **Title tag** unique: `Jasa Tebas Rumput {Area} — Potong Rumput Mesin Murah {Area} {Region}`
2. **Meta description** unique + **keywords** unique (inject area name).
3. **Canonical** → `https://domain/wilayah/{slug}/`
4. **H1** contains area name (e.g. `Jasa Tebas & Potong Rumput di {Area}`).
5. **Content 500–800 words** — spun across templates so no two pages are duplicates. Spintax `{a|b|c}`, resolve with the pipe-only regex (see SKILL.md pitfall #1).
6. **JSON-LD ×2**: `HomeAndConstructionBusiness` (name/telephone/address/areaServed = the area) + `FAQPage` (3 Q&A localized to the area).
7. **Silo internal links**: "Area Layanan Lainnya di {region}" cross-linking every sibling area page.
8. **WhatsApp CTAs** carrying `?text=...di {area}` so inbound leads are pre-qualified.

## kalsel_gen.py usage

Edit top-of-file constants then run:
- `AREAS` — list of `(slug, nama_area, tipe, parent_region)` tuples. Base card has ~42 Kalsel areas; extend with all kecamatan to go 100+.
- `PHONE` (display) / `PHONE_INTL` (+62) / `WA_NUMBER` (62...) / `DOMAIN`.

```bash
python3 kalsel_gen.py --seed 42 --out site
# emits: site/wilayah/<slug>/index.html  +  sitemap.xml  +  robots.txt  +  pages_catalog.csv
```

Verify before deploy:
```bash
python3 -c "
import re, json
html = open('site/wilayah/gambut/index.html').read()
for b in re.findall(r'<script type=\"application/ld\+json\">(.*?)</script>', html, re.DOTALL):
    print(json.loads(b)['@type'])
"
```

Local preview: `cd site && python3 -m http.server 8899` (run terminal background=true), then `curl localhost:8899/wilayah/<slug>/`.

## Deploy + indexing (the part that actually makes it "FYP")

1. `vercel deploy site --prod` (or drag folder into vercel.com dashboard). Domain already proxied through Vercel → pages just go live.
2. Google Search Console → verify domain → submit `https://domain/sitemap.xml`.
3. Register a **Google Business Profile** (free) so the LocalBusiness schema + GBP reinforce local-pack ranking.

## Caveat

Orphan pages never rank — internal linking (pitfall #5) is what turns 42 pages into a crawled topical cluster. Also stagger sitemap discovery: don't dump 100+ near-duplicate pages at once if content is too thin; Google may treat them as doorway pages and deindex. Sentence-level spinning + genuine area-specific details (actual landmarks/streets) is the defense.