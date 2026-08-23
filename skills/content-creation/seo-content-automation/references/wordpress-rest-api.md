# WordPress REST API — Bulk Posting Reference

## Endpoints
- Create post: `POST {site}/wp-json/wp/v2/posts`
- Upload media: `POST {site}/wp-json/wp/v2/media` (multipart, field name `file`)
- List categories: `GET {site}/wp-json/wp/v2/categories`
- List tags: `GET {site}/wp-json/wp/v2/tags`

## Auth — Application Password (REQUIRED, not login password)
WP rejects REST API auth with the normal login password unless using an Application Password.

### How to create an Application Password (WP Admin)
1. Login → **Users → Profile** (or **Users → All Users → edit**)
2. Scroll to **Application Passwords**
3. Enter a name (e.g. "CSV2Post"), click **Add New Application Password**
4. Copy the generated `xxxx xxxx xxxx xxxx xxxx` key (shown ONCE)

### Header
```
Authorization: Basic base64("username:application_password")
```
Note: if the site is behind HTTP Basic Auth (htpasswd) or a login-popup, pass that separately as `--basic-user`/`--basic-pass` in csv2post.py — it is distinct from the WP Application Password.

## POST body fields (wp/v2/posts)
```json
{
  "title": "string",
  "content": "HTML string",
  "excerpt": "string",
  "status": "draft|publish|pending|private|future",
  "slug": "string",
  "author": 1,
  "categories": [1, 3],
  "tags": [4, 5],
  "featured_media": 123,
  "meta": { "custom_field": "value" }
}
```
- `categories`/`tags` accept **IDs** (integers), or you can pass slugs by name for categories (strings).
- `featured_media` must be a media attachment ID — upload first via `/media`, then reference the returned `id`.
- `meta` requires the field to be registered (e.g. via `register_post_meta`) or REST will reject.

## Common errors
- `401 rest_cannot_create` → wrong/missing Application Password, or user lacks `edit_posts` capability.
- `403 rest_forbidden` → status not allowed (e.g. subscriber trying to `publish`) or user can't edit that post type.
- `400 rest_invalid_param` → bad field value (e.g. category ID as string, invalid status enum).

## csv2post.py column mapping (`--map` flag)
Default mapping expects CSV columns: `title,content,excerpt,categories,tags,featured_image`.
To remap non-standard columns: `--map title=judul --map content=isi --map categories=kat_id`.
Categories/tags in CSV are comma-separated integer IDs. Featured image cell holds a local file path — script auto-uploads it.