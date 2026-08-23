# HFM API Architecture — Full JS Bundle Extraction

Extracted from Next.js chunk `89067-112fa225fdaded66.js` on `my.hfm.com/id/webtrader`.

## Vault References (all under `hfprojectskv` mount)

### API Base URLs
| Vault Key | Purpose |
|-----------|---------|
| `ACCOUNT-HF-API_BASE_URL` | Account management |
| `AFFILIATES-INT-HF-API_BASE_URL` | Affiliate/internal |
| `AUTHENTICATION-HF-API_BASE_URL` | Auth service |
| `APP-HF-API_BASE_URL` | Mobile app backend |
| `ASSISTANT-HF-AFFILIATES-API_BASE_URL` | Affiliate assistant |
| `ASSISTANT-HF-API_BASE_URL` | Customer assistant |
| `BIG-REPORTS-HF-API_BASE_URL` | Reporting |
| `SEMINAR-QR-HF-API_BASE_URL` | Seminar QR |
| `COPY-HF-API_BASE_URL` | Copy trading |
| `CMS-HF-API_BASE_URL` | Content management |
| `CMS-HF-FRONTEND_BASE_URL` | CMS frontend |
| `CRONS-WEBHOOK_BASE_URL` | Cron webhooks |
| `ELASTIC-HF-API_BASE_URL` | Elasticsearch API |
| `ELASTIC-SEARCH_BASE_URL` | Elasticsearch direct |
| `MAILER-HF-API_BASE_URL` | Email service |
| `MANAGER-HF-API_BASE_URL` | Account manager |
| `MONGO-INTERNAL-HF-API_BASE_URL` | MongoDB internal |
| `MOBILE-HF-FRONTEND_BASE_URL` | Mobile frontend |
| `ONBOARDING-HF-API_BASE_URL` | User onboarding |
| `PAMM-HF-API_BASE_URL` | PAMM accounts |
| `PAYMENTS-HF-API_BASE_URL` | Payments |
| `PAYMENTS-INT-HF-API_BASE_URL` | Internal payments |
| `PAYMENTS-EXT-HF-API_BASE_URL` | External payments |
| `PSP-HF-API_BASE_URL` | Payment service provider |
| `REGISTRATION-HF-API_BASE_URL` | User registration |
| `VAULT-HF-API_BASE_URL` | Vault proxy |
| `WALLET-HF-API_BASE_URL` | Wallet service |
| `WEBS-API_BASE_URL` | Website API |

### Platform REST API (MT5 Gateway)
| Vault Key | Value |
|-----------|-------|
| `PLATFORM-REST-API_AUTHENTICATION_USER` | Basic auth username |
| `PLATFORM-REST-API_AUTHENTICATION_PASSWORD` | Basic auth password |
| (Demo variant has separate credentials) | |

### Third-Party Integrations
| Vault Key | Service |
|-----------|---------|
| `NUMVERIFY_ACCESS_KEY` | Phone verification |
| `NUMVERIFY_ANDROID_AUTOFILL_CODE` | Android autofill |
| `SINCH_PHONE_VERIFICATION_*` | Sinch SMS/voice verification |
| `SINCH_CALLING_API_BASE_URL` | Sinch calling API |
| `TIN_CHECK_TINCHECK_*` | Tax ID verification |
| `TWILIO_API_BASE_URL` | Twilio |
| `TWILIO_ACCOUNT_SID` | Twilio SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth |
| `TWILIO_SERVICE_SID` | Twilio service |
| `FXBLUE_BROKERID` | FXBlue analytics |
| `FXBLUE_PASSWD` | FXBlue password |
| `FXBLUE_USR` | FXBlue username |
| `SIGNABLE_SIGNABLE_*` | e-Signature |
| `SOLITICS_API_BASE_URL` | Solitics marketing |
| `SOLITICS_REGISTER_MEMBER_ENDPOINT` | Solitics registration |
| `SOLITICS_ACCESS_KEY` | Solitics access |
| `SOLITICS_SECRET_KEY` | Solitics secret |
| `MAILWIZZ_PUBLIC_KEY` | Mailwizz email |
| `MAILWIZZ_PRIVATE_KEY` | Mailwizz private |
| `NEW_RELIC_LICENSE_KEY` | APM monitoring |

## Resolved URLs Found in JS Bundle

- `https://platforms-rest-api-live.hfmarkets.com` — MT5 live gateway
- `https://platforms-rest-api-demo.hfmarkets.com` — MT5 demo gateway
- `https://calling.api.sinch.com/calling/v1/callouts` — Sinch voice
- `https://sms.api.sinch.com/xms/v1/` — Sinch SMS

## Infrastructure Notes

- Platform REST API demo server: Apache/2.4.41 on Ubuntu, internal IP `10.10.101.200`
- All services behind Cloudflare
- WebTrader uses Next.js RSC (React Server Components) with WebSocket for real-time data
- `WEB_SOCKET_MAX_RECONNECTIONS` constant found in JS — WebSocket reconnection logic
- Sinch phone verification with 7s connect/request timeouts

## Sniffing Methodology

1. Fetch WebTrader page via `curl_cffi` with `impersonate=chrome` + DataImpulse proxy
2. Extract JS chunk URLs from HTML (`/_next/static/chunks/*.js`)
3. Download each chunk and grep for `BASE_URL`, `from_vault`, `wss://`, `ws://`, `api/v`
4. The chunk `89067-112fa225fdaded66.js` contained all API service definitions
5. Platform REST API URLs appear as string literals, not vault references