---
name: seo-content-automation
description: Use when bulk-generating SEO/spun content or mass-posting.
---

# SEO Content Automation — Mass Generation & Bulk Posting

Build pipeline that turns a product/service keyword into hundreds/thousands of unique location-based articles and auto-posts them to a CMS for SEO traffic ("FYP"/Discover-style local ranking).

## When to use
- User wants to "auto spam post" for SEO traffic, "biar website fyp", or mass article generation
- Need product × city × template content spins (e.g. "Kontraktor Sauna Kayu Kota Medan", "Jual X Kota Y")
- Bulk-post CSV to WordPress via REST API

## Core tools (in `/home/ubuntu/csv2post/`)
- `seo_gen.py` — generates N unique articles from {product} × {city} × {spintax templates}, outputs CSV. Pre-loaded with ~110 Indonesian cities + 12 keyword prefixes + 5 content templates.
- `csv2post.py` — bulk-posts CSV to WordPress via REST API (`wp-json/wp/v2/posts`), Auth via Application Password (or Basic), supports category/tag IDs, featured image upload, dry-run, delay, custom column mapping.
- `kalsel_gen.py` — programmatic SEO for STATIC sites: generates 1 full landing page per geographic area (kecamatan/kelurahan) with unique title/meta/H1/content/schema + `sitemap.xml` + `robots.txt`, ready for Vercel/GitHub-Pages deploy. See `references/programmatic-local-seo.md`.

## Workflow

### A. WordPress/blog target → CSV → REST API
1. Generate: `python3 seo_gen.py "Sauna Kayu" --num 1000 --phone 0812xxx --seed 42 --out mass.csv`
2. Dry-run check: `python3 csv2post.py mass.csv --url https://wp.site --user admin --app-pass "xxxx xxxx xxxx xxxx xxxx" --dry-run`
3. Live post: same command minus `--dry-run`, add `--status draft|publish --delay 5`.
4. For mass scale, register site in Google Search Console and throttle posting (5–15/min) to avoid thin-content deindex.

### B. Static site (Vercel/Netlify/GitHub Pages) → programmatic local SEO
**Detect first**: `curl -sIL https://site | grep -i server` — if it says `Vercel`/`Netlify` and body is a hand-written `<html>` (not `wp-content`), do NOT use csv2post. It has no REST API.
1. Extract the existing site's design (curl the live HTML, read `/tmp/*.html`).
2. Run `kalsel_gen.py` (edit `AREAS`, `PHONE`, `DOMAIN` at top) → emits `site/wilayah/<slug>/index.html` per area + sitemap + robots.
3. Verify schema: parse `ld+json` blocks, assert `@type` present, assert `<title>`/`<h1>` contain the area name.
4. Deploy folder to Vercel (`vercel deploy site --prod`) and submit sitemap in Search Console.
Full detail + pitfalls in `references/programmatic-local-seo.md`.

## Pitfalls (learned the hard way)

### 1. Spintax regex MUST only match braces containing a pipe
A naive `re.sub(r'\{([^{}]*)\}', ...)` eats `{prefix}`/`{product}`/`{city}`/`{phone}` format placeholders too, leaving literal "prefix", "product" in output. Fix: only resolve braces with a `|` inside:
```python
pattern = re.compile(r'\{([^{}]*\|[^{}]*)\}')   # matches {a|b}, NOT {prefix}
# then .format(prefix=..., product=..., city=..., phone=...) on the unspun text
```
Order matters: unspin first, then `.format()` for placeholders.

### 2. Don't shadow a loop parameter with `rng.choice()`
`phone = rng.choice(phone)` reassigns the list param to a string; the next iteration calls `rng.choice("0812-...")` which picks a RANDOM CHARACTER ("2", "-", "0"). Symptom: phone numbers corrupted to single digits. Fix: use a fresh variable `this_phone = rng.choice(phone)`.

### 3. WordPress auth = Application Password (not login password)
WP blocks REST API with the normal login password. User must create an Application Password (WP Admin → Users → Profile → Application Passwords). Pass it as `--app-pass`. Script builds `Authorization: Basic base64(user:app_pass)`.

### 4. JSON-LD schema inside an f-string → build it OUTSIDE the template
Nesting `json.dumps([{"@type": ...} for f in faqs])` directly inside a triple-quoted f-string that also has escaped `{{ }}` (e.g. Tailwind config `tailwind.config = {{ ... }}`) throws `TypeError: unhashable type: 'dict'`. The escaped braces and the dict literals collide. Fix: build the schema as a plain variable FIRST, then inject the single placeholder:
```python
biz_schema = json.dumps({...}, ensure_ascii=False)
faq_json   = json.dumps({...}, ensure_ascii=False)
page = f'''... <script type="application/ld+json">{biz_schema}</script> ...'''
```

### 5. Internal linking = mandatory for programmatic pages
A page nobody links to is an orphan — Google won't crawl it well. Group areas by parent region and inject a "Area Layanan Lainnya di {region}" cross-link block into every page (silostructure → crawlable + topical authority). Build a `defaultdict(list)` mapping `parent_region → [(slug, name)]` and pass siblings into the page builder.

## Platform cheat-sheet for SEO spam traffic (easiest → hardest to auto-post)
- **Blogger/Blogspot** — email-to-post + API, Google-owned so indexes fast, unlimited free blogs, BEST for mass spam.
- **WordPress self-hosted** — REST API (these tools), full control, cheap hosting (~Rp15rb/mo).
- **WordPress.com** — same REST API but spam-suspend risk.
- **Wix** — needs Velo API key, clunky, skip for mass auto-post.
- **Medium** — strong anti-bot, hard to automate.
- **Google Sites / Notion+Super.so** — no API / manual, only for 1-2 landing pages.

⚠️ Honest caveat: heavily spun thin content gets deindexed by Google. Spin at sentence level (not just word swap), throttle posting, mix with original content.

## References
- `references/wordpress-rest-api.md` — WP REST API endpoints, Application Password auth, field mappings.
- `references/programmatic-local-seo.md` — static-site programmatic SEO pattern: detect Vercel/static, area-page anatomy (schema/LocalBusiness/FAQPage/silo links), full kalsel_gen.py usage.