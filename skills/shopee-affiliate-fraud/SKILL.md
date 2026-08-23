---
name: shopee-affiliate-fraud
description: Use when exploiting Shopee/ShopeeFood affiliate programs.
tags: [shopee, affiliate, cookie-injection, redirect, shopeefood, commission, indirect-order, device-fingerprint]
---

# Shopee Affiliate Fraud — Cookie Injection + Redirect Rotator

Comprehensive toolkit for manipulating Shopee Affiliate tracking. Built from real Indonesian affiliate techniques and live testing.

## Trigger

"shopee affiliate", "komisi shopee", "shopeefood", "affiliate tanpa order", "cookie shopee", "redirect shopee"

## Quick Start

```bash
# Cookie injection test with device fingerprints
python3 shopee_cookie_test.py --affiliate-link "https://s.shopee.co.id/XXXXX" --direct --count 20

# PHP redirect rotator (upload to server)
# Edit shopee_redirect.php → add your affiliate links → deploy

# Clickbait post generator
python3 shopee_indo_trick.py --affiliate-id YOUR_ID --product "https://shopee.co.id/product/..."

# Last-click hijack simulation
python3 shopee_hijack.py --affiliate-id YOUR_ID --mode last-click --product "..."
```

## Shopee Affiliate Mechanics (from official docs)

| Mechanic | Detail |
|----------|--------|
| Cookie window | 7 days after click |
| Attribution | **Last-click** — last affiliate link clicked before checkout wins |
| Validation | Order must be COMPLETED (delivered + return period passed, ~60 days) |
| Direct Order | Buyer purchases from same shop → full commission |
| Indirect Order (2026) | Buyer purchases from DIFFERENT shop → 50% of seller rate |
| ShopeeFood New Buyer | 50% commission (max Rp10,000/item) for same-restaurant orders |
| Commission per item | ShopeeFood counts per MENU ITEM, not per order |

## Reality Check

**Shopee is CPS (Cost Per Sale). You CANNOT get commission without a real completed order.**

- ❌ No simulated/fake orders
- ❌ No postback spoofing (Shopee uses internal API, not public postback)
- ❌ Cookie-only = no commission without purchase
- ✅ Cookie injection WORKS for tracking clicks
- ✅ Indirect orders: ANY purchase within 7 days = commission
- ✅ Last-click hijack: overwrite another affiliate's cookie

## Techniques

### 1. Cookie Injection + Redirect Rotator
The Indonesian technique: wrap affiliate links in redirect page, inject realistic cookies, share via clickbait.

```
PHP redirect page → random affiliate link → 7-day cookie injected
User buys ANYTHING in 7 days → commission earned
```

### 2. Indirect Order Farming
Link ANY popular product → user buys ANYTHING else → you get 50% of that seller's rate (2026 update).

### 3. ShopeeFood New Buyer
50% commission for new buyers. Target: people who never used ShopeeFood. Share restaurant links in food groups.

### 4. Last-Click Hijack
Inject your affiliate cookie just before user checks out → overwrite previous affiliate's tracking.

## Pitfalls

- **Broken short links**: `s.shopee.co.id` links can return error_page. Always test each link before deploying.
- **Shopee TOS Section 6.5**: Explicitly prohibits cookie dropping, iframes, pop-ups, automatic redirects. Account ban risk.
- **Self-purchase detection**: Shopee tracks address, device ID, account connections. Don't buy from your own links.
- **DM/private message links not tracked**: Shopee doesn't count 1-on-1 shared links. Must be public posts.
- **Shopee Video/Livestream hijack**: If user watches a Shopee Video or Live after clicking your link, the video/livestream link wins last-click attribution.
- **Cashback app interference**: ShopBack, etc. overwrite affiliate cookies — user loses your attribution.
- **0đ orders**: Voucher making total = 0 → no commission.
- **Validation delay**: ~60 days from order to confirmed commission.

## Files

```
/home/ubuntu/shopee_redirect.php       # PHP redirect rotator with cookie injection
/home/ubuntu/shopee_cookie_test.py     # Python traffic simulator + device fingerprints
/home/ubuntu/shopee_indo_trick.py      # Clickbait post generator (bit.ly + viral templates)
/home/ubuntu/shopee_hijack.py          # Last-click hijack + cookie injection toolkit
/home/ubuntu/affiliate_fraud.py        # General affiliate fraud (cookie stuffing + click sim)
```

## Device Fingerprint Pool

The PHP redirector and Python tester include realistic Indonesian device profiles:
- 20+ device models (Samsung, Xiaomi, OPPO, vivo, iPhone, Realme, Infinix)
- 7 carriers (Telkomsel, Indosat, XL, Tri, Smartfren, IndiHome, Biznet)
- 16+ cities across Indonesia
- Realistic User-Agent strings per device
- Google Analytics & Facebook tracking cookies
- Shopee-specific cookies (SPC_EC, SPC_F, SPC_SI, etc.)

## References

- `references/shopee-affiliate-official-docs.md` — Compiled official Shopee Affiliate documentation
- `references/shopee-indonesian-tricks.md` — Real Indonesian affiliate techniques from blog research