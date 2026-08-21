#!/usr/bin/env python3
"""Fetch a full X/Twitter thread with untruncated text and images — no auth.

Two free, no-auth endpoints do the whole job (X's paid API is a red herring):

  - syndication API  -> metadata, engagement, reply chain (in_reply_to), image URLs
  - fxtwitter API    -> the FULL note-tweet text (syndication truncates at 280)

Usage:
  ./fetch_thread.py <tweet_url_or_id> [--last <url_or_id>] [-o OUTDIR] [--no-images]

If you pass --last, walking starts from the last post backward to the root via
in_reply_to; otherwise the single tweet and any single-chain ancestors are pulled.

Outputs:
  OUTDIR/thread.json     structured posts (text, media, urls, metrics)
  OUTDIR/thread.md       human-readable thread
  OUTDIR/images/*.jpg    all photos at full resolution
  OUTDIR/raw/*.json      raw API responses (for re-parse)
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
SYND = "https://cdn.syndication.twimg.com/tweet-result?id={}&token=0"
FX = "https://api.fxtwitter.com/{}/status/{}"


def tweet_id(s: str) -> str:
    m = re.search(r"/status/(\d+)", s or "")
    return (m.group(1) if m else s or "").strip()


def user_handle(s: str) -> str | None:
    m = re.search(r"(?:x\.com|twitter\.com)/([A-Za-z0-9_]+)/status", s or "")
    return m.group(1) if m else None


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read()


def synd(tid: str) -> dict:
    return json.loads(get(SYND.format(tid)))


def fx(tid: str, handle: str | None) -> dict | None:
    if not handle:
        return None
    try:
        return json.loads(get(FX.format(handle, tid)))
    except Exception:
        return None  # fxtwitter occasionally 404s; syndication text is the fallback


def walk_chain(last_id: str, root_hint: str | None = None) -> list[dict]:
    """Walk backward from last_id via in_reply_to until no parent or root reached."""
    chain, seen, tid = [], set(), last_id
    while tid and tid not in seen:
        seen.add(tid)
        try:
            d = synd(tid)
        except Exception as e:
            print(f"  syndication fetch failed for {tid}: {e}", file=sys.stderr)
            break
        chain.append(d)
        parent = d.get("in_reply_to_status_id_str")
        if root_hint and tid != root_hint and parent == root_hint:
            try:
                chain.append(synd(root_hint))
            except Exception:
                pass
            break
        if not parent:  # reached root (no parent = thread origin)
            break
        tid = parent
        time.sleep(0.2)
    chain.reverse()  # oldest -> newest
    return chain


def merge(d: dict, handle: str | None) -> dict:
    """One post: full text from fxtwitter (untruncated), fallback to syndication."""
    tid = d.get("id_str", "")
    f = fx(tid, handle)
    fx_text = (f or {}).get("tweet", {}).get("text")
    synd_text = d.get("text", "")
    text = fx_text if fx_text and len(fx_text) >= len(synd_text) else synd_text
    src = "fxtwitter" if fx_text and len(fx_text) >= len(synd_text) else "syndication"
    media = []
    for m in d.get("mediaDetails", []) or []:
        media.append({
            "type": m.get("type"),
            "image": m.get("media_url_https"),
            "alt": m.get("ext_alt_text") or "",
        })
    urls = [u.get("expanded_url") for u in d.get("entities", {}).get("urls", [])]
    mentions = [m.get("screen_name") for m in d.get("entities", {}).get("user_mentions", [])]
    return {
        "id": tid, "created_at": d.get("created_at"),
        "in_reply_to": d.get("in_reply_to_status_id_str"),
        "text": text, "text_len": len(text), "source": src,
        "media": media, "urls": urls, "user_mentions": mentions,
        "favorite_count": d.get("favorite_count"),
        "bookmark_count": d.get("bookmark_count"),
    }


def download_images(posts: list[dict], imgdir: str) -> None:
    os.makedirs(imgdir, exist_ok=True)
    for p in posts:
        for j, m in enumerate(p["media"]):
            if m["type"] != "photo" or not m["image"]:
                continue
            base = m["image"].rsplit("/", 1)[-1].split(".")[0]
            name = f"{p['index']}_{base}.jpg"
            url = f"{m['image']}?format=jpg&name=large"
            try:
                open(os.path.join(imgdir, name), "wb").write(get(url))
                m["saved"] = name
                print(f"  image -> images/{name}")
            except Exception as e:
                print(f"  image fetch failed {url}: {e}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tweet", help="tweet URL or id (the root, or any post in the thread)")
    ap.add_argument("--last", help="URL or id of the LAST post (enables full backward chain walk)")
    ap.add_argument("-o", "--out", default="thread_out", help="output directory")
    ap.add_argument("--no-images", action="store_true")
    args = ap.parse_args()

    handle = user_handle(args.tweet) or user_handle(args.last or "")
    start = tweet_id(args.last) if args.last else tweet_id(args.tweet)
    root_hint = tweet_id(args.tweet) if args.last else None

    print(f"walking from {start}" + (f" to root {root_hint}" if root_hint else ""))
    raw = walk_chain(start, root_hint)
    print(f"chain length: {len(raw)}")

    posts = []
    for i, d in enumerate(raw):
        p = merge(d, handle)
        p["index"] = i
        posts.append(p)

    out = args.out.rstrip("/")
    rawdir = os.path.join(out, "raw")
    os.makedirs(rawdir, exist_ok=True)
    for d in raw:
        json.dump(d, open(os.path.join(rawdir, f"synd_{d.get('id_str')}.json"), "w"), indent=2)

    json.dump(posts, open(os.path.join(out, "thread.json"), "w"), indent=2)

    # markdown
    md = []
    for p in posts:
        md.append(f"## [{p['index']}] `{p['id']}` ({p['text_len']} chars, {p['source']})\n")
        md.append(p["text"] + "\n")
        if p["media"]:
            for m in p["media"]:
                md.append(f"_image: {m.get('saved') or m['image']}_ alt={m['alt']!r}")
        if p["urls"]:
            for u in p["urls"]:
                md.append(f"link: {u}")
        md.append("")
    open(os.path.join(out, "thread.md"), "w").write("\n".join(md))

    if not args.no_images:
        download_images(posts, os.path.join(out, "images"))
        json.dump(posts, open(os.path.join(out, "thread.json"), "w"), indent=2)  # rewrite with saved names

    # completeness check: a post is only suspect if fxtwitter FAILED (source=syndication)
    # AND its text is near the 280 truncation ceiling.
    trunc = [p["id"] for p in posts if p["source"] == "syndication" and p["text_len"] >= 270]
    print(f"\ndone: {len(posts)} posts -> {out}/")
    if trunc:
        print(f"WARNING: truncated posts (fxtwitter returned no full text): {trunc}", file=sys.stderr)
        print("retry with the author handle in the URL, or pass --last from a URL containing the handle.", file=sys.stderr)


if __name__ == "__main__":
    main()
