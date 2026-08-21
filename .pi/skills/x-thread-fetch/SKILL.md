---
name: x-thread-fetch
description: Fetch a full X/Twitter thread — all posts with untruncated text plus images — without auth or the paid API. Use when the user wants to retrieve, extract, scrape, pull, save, or download an X/Twitter thread, tweet text, or tweet images, mentions a status URL or tweet id, or asks to get the content of a thread/post.
---

# X thread fetch

Retrieve a complete X/Twitter thread deterministically. **No login, no API key, no paid tier.** Two free no-auth endpoints cover everything; the script below runs them.

The key insight that costs the most to rediscover: **X's note tweets (long-form posts) are truncated at 280 chars by the metadata endpoint.** A second endpoint unfurls the full text. Skipping the second gives you silently incomplete threads — posts ending mid-sentence ("...solved 2 more", "...On Deck:").

## The two endpoints

- **Syndication** (`cdn.syndication.twimg.com/tweet-result?id=<id>&token=0`) — metadata, engagement counts, the reply chain (`in_reply_to_status_id_str`), and image URLs (`mediaDetails`). **Truncates note tweets.**
- **Unfurl** (`api.fxtwitter.com/<handle>/status/<id>`) — the **full untruncated note-tweet text**. Needs the author handle (take it from the status URL).

## Process

1. **Get the IDs.** Accept a status URL or bare id. The script walks the reply chain backward (via `in_reply_to_status_id_str`) until it reaches the root post (no parent) — so **any single post in the thread is enough**. `--last` is an optional convenience when you only have the last/mid post handy, or want to be explicit; passing the root URL alone fetches the full thread.

2. **Run the script** — it walks the reply chain backward via syndication, unfurls each post's full text, downloads images, and writes `thread.json` + `thread.md` + `images/`:
   ```sh
   ./fetch_thread.py "<any-post-url>" [-o <outdir>] [--last "<last-post-url>"]
   ```
   Always pass the **full status URL** (not a bare id) so the author handle is extracted for the unfurl endpoint.

3. **Verify completeness** — the script exits non-zero silently only on network failure; it prints `WARNING: truncated posts` only when the unfurl endpoint failed for specific ids. The completion criterion: **zero truncation warnings AND every post's `source` is `fxtwitter`** (or the post is genuinely short). If a warning fires, re-run with the handle in the URL, or the unfurl service is down — fall back to the syndication `text` and flag those posts as incomplete to the user rather than guessing.

4. **Images** download at `?format=jpg&name=large` (full res). Videos/animated GIFs: the script currently pulls photos only; note this if the thread has video.

Do not use `fetch_content`, X's logged-in pages, or browser automation for retrieval — they fail (JS-gated / login-walled) and the two endpoints above already return structured data faster. Reach for the browser only if both endpoints are down for a specific tweet.

## What you get

`thread.json` (structured: `text`, `text_len`, `source`, `media`, `urls`, `user_mentions`, engagement), `thread.md` (readable), `images/*.jpg`, and `raw/*.json` (API responses, for re-parse). Posts are ordered oldest → newest with a `index` field.
