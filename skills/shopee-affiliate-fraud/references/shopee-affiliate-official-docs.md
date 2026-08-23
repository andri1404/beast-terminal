# Shopee Affiliate — Official Documentation Summary

Compiled from Shopee Help Center, Seller Education Hub, and official API docs.

## Commission Model

- **CPS (Cost Per Sale)**: Commission only on completed, validated orders
- **7-day cookie window** after click
- **Last-click attribution**: Last affiliate link clicked before checkout wins
- **Validation**: Order must be delivered + pass return/refund period (~60 days)
- **Payout**: Weekly, minimum threshold varies by country

## Order Types (2026 Update)

| Type | Definition | Commission |
|------|-----------|------------|
| Direct Order | Same shop as linked | 100% of seller rate |
| Indirect Order | Different shop from linked | 50% of seller rate (from 24 May 2026) |

## Commission Structure

```
Shopee Commission (Base): 2.5%–12% per category
Commission XTRA (Seller): Up to 40% bonus from sellers
Total Possible: Up to 50%+ on some products
```

Capped at RM5 per completed order for Shopee Commission.

## ShopeeFood Affiliate

- Commission per MENU ITEM, not per order
- New Buyer + Same Restaurant: 50% (max Rp10,000/item)
- New Buyer + Different Restaurant: 8% (max Rp10,000/item)
- Existing Buyer + Same Restaurant: 15% (max Rp10,000/item)
- Existing Buyer + Different Restaurant: 8% (max Rp10,000/item)

## Prohibited (TOS Section 6.5)

- Cookie dropping without user consent
- iFrames, pop-ups, pop-unders
- Automatic redirects without user action
- Postview technology
- Misleading advertisements
- Forced app installations
- Self-purchase through own affiliate links

## API Access

Shopee provides GraphQL API for affiliates:
- `generateShortLink` — Create affiliate links
- `conversionReport` — Get conversion data
- `validatedReport` — Get validated (paid) commissions

App ID + Secret required. No public postback/webhook endpoint.

## Tracking Parameters

```
affiliate_id={id}          — Affiliate identifier
sub_id={sub1}-{sub2}-...   — Up to 5 sub-IDs (appears as utmContent)
utm_medium=affiliates      — Auto-set
utm_campaign={campaign}    — Campaign tracking
uls_trackid={auto}         — Auto-populated by Shopee
utm_term={auto}            — Auto-populated by Shopee
```

## Short Link Format

```
https://s.shopee.co.id/{shortcode}     — Official Shopee short link
https://shp.ee/{shortcode}              — Alternative short domain
```

Source: Shopee Help Center, Seller Education Hub, shopee.co.id, affiliate API docs (bcat95/shopee-aff)