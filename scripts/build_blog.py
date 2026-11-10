"""Build the clinician blog from Markdown posts.

Posts live in posts/*.md and start with a front-matter block:

    ---
    title: Making Intake Forms Screen-Reader Friendly
    date: 2027-02-14
    summary: One or two sentences shown on the blog list.
    ---
    Post body in Markdown...

Run:  python3 scripts/build_blog.py
Writes blog.html (the list), blog-<slug>.html (one page per post), and
refreshes the "latest posts" box on resources.html between the
BLOG:START / BLOG:END markers. Page chrome (header, nav, footer, fonts)
is copied from resources.html so the blog always matches the site.
"""
import datetime as dt
import html
import pathlib
import re

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts"
BASE_URL = "https://notcraven.github.io/cort-site/"
BLOG_NAME = "Accessible Practice"
BLOG_TAGLINE = "A blog for clinicians on making therapy accessible."
B = "'Bangers', Impact, 'Arial Narrow', sans-serif"

POST_CSS = """
.post-body{font-size:19px;line-height:1.75}
.post-body h2{font-family:'Bangers',Impact,'Arial Narrow',sans-serif;font-weight:400;font-size:36px;letter-spacing:1px;line-height:1.1;margin:44px 0 12px}
.post-body h3{font-weight:900;font-size:22px;margin:32px 0 8px}
.post-body h4{font-weight:900;font-size:17px;letter-spacing:1px;text-transform:uppercase;color:#5B2FC2;margin:26px 0 8px}
.post-body p{margin:0 0 20px}
.post-body ul,.post-body ol{margin:0 0 20px;padding-left:28px}
.post-body li{margin-bottom:8px}
.post-body a{color:#5B2FC2;font-weight:700}
.post-body a:hover{color:#141414}
.post-body blockquote{margin:28px 0;padding:18px 22px;background:#FFD83B;border:4px solid #141414;box-shadow:6px 6px 0 #141414;font-weight:600}
.post-body blockquote p:last-child{margin:0}
.post-body img{display:block;max-width:100%;height:auto;border:4px solid #141414;margin:28px 0}
.post-body code{background:#FFFFFF;border:2px solid #141414;padding:1px 6px;font-size:.9em}
.post-body table{border-collapse:collapse;width:100%;margin:0 0 24px;background:#FFFFFF;border:3px solid #141414;font-size:17px}
.post-body th,.post-body td{border:2px solid #141414;padding:8px 10px;text-align:left;vertical-align:top}
.post-body th{background:#141414;color:#FFF8E7}
"""


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        raise SystemExit(f"{path.name}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip().strip('"')
    for k in ("title", "date", "summary"):
        if not meta.get(k):
            raise SystemExit(f"{path.name}: front matter needs '{k}'")
    meta["date_obj"] = dt.date.fromisoformat(meta["date"])
    meta["slug"] = meta.get("slug") or re.sub(r"[^a-z0-9]+", "-", meta["title"].lower()).strip("-")
    body = markdown.markdown(m.group(2), extensions=["extra", "sane_lists", "smarty"])
    # external links open in a new tab, announced to screen readers
    body = re.sub(r'<a href="(https?://[^"]+)">(.*?)</a>',
                  r'<a href="\1" target="_blank" rel="noopener">\2<span class="sr-only"> (opens in a new tab)</span></a>', body)
    meta["html"] = body
    return meta


def nice_date(d):
    return f"{d:%B} {d.day}, {d.year}"


def chrome():
    page = (ROOT / "resources.html").read_text(encoding="utf-8")
    head, rest = page.split('<main id="main"', 1)
    tail = rest.split("</main>", 1)[1]
    return head, tail


def page(head, tail, title, desc, url, main):
    e = lambda s: html.escape(s, quote=True)
    h = re.sub(r"<title>.*?</title>", f"<title>{e(title)}</title>", head, count=1)
    for prop, val in (("description", desc),):
        h = re.sub(rf'<meta name="{prop}" content="[^"]*">', f'<meta name="{prop}" content="{e(val)}">', h, count=1)
    h = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{e(title)}">', h, count=1)
    h = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{e(desc)}">', h, count=1)
    h = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', h, count=1)
    h = h.replace("</style>", POST_CSS + "</style>", 1)
    return h + '<main id="main" tabindex="-1" style="outline: none">\n' + main + "\n</main>" + tail


def card(p, heading="h2"):
    return (f'<article style="background: #FFFFFF; border: 4px solid #141414; box-shadow: 8px 8px 0 #141414; padding: 22px 24px; display: flex; flex-direction: column; gap: 8px">'
            f'<span style="font-size: 13px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: #4A4A4A">{nice_date(p["date_obj"])}</span>'
            f'<{heading} style="margin: 0; font-family: {B}; font-weight: 400; font-size: 30px; letter-spacing: 1px; line-height: 1.1"><a href="blog-{p["slug"]}.html" style="color: #141414; text-decoration: none">{html.escape(p["title"])}</a></{heading}>'
            f'<p style="margin: 0; font-size: 17px; line-height: 1.6">{html.escape(p["summary"])}</p>'
            f'<a href="blog-{p["slug"]}.html" style="align-self: flex-start; font-weight: 900; font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px; min-height: 44px; display: flex; align-items: center; color: #141414">Read the post<span class="sr-only">: {html.escape(p["title"])}</span> →</a>'
            f'</article>')


def main():
    POSTS.mkdir(exist_ok=True)
    posts = sorted((parse(p) | {"mtime": p.stat().st_mtime} for p in POSTS.glob("*.md")),
                   key=lambda p: (p["date_obj"], p["mtime"]), reverse=True)  # same date: most recently added first
    head, tail = chrome()

    hero = (f'<section class="ht-yellow" style="border-bottom: 4px solid #141414">\n'
            f'<div style="max-width: 1080px; margin: 0 auto; padding: 64px 24px; display: flex; flex-direction: column; align-items: center; gap: 20px; text-align: center">\n'
            f'<span style="background: #FFF8E7; border: 3px solid #141414; padding: 6px 12px; font-weight: 900; font-size: 13px; letter-spacing: 2px">FOR CLINICIANS</span>\n'
            f'<h1 style="margin: 0; background: #19B8C9; border: 5px solid #141414; box-shadow: 10px 10px 0 #141414; padding: 14px 32px; font-family: {B}; font-weight: 400; font-size: clamp(44px, 6vw, 76px); line-height: 1; letter-spacing: 2px; transform: rotate(-2deg)">{BLOG_NAME.upper()}</h1>\n'
            f'<p style="margin: 0; background: #FFF8E7; border: 3px solid #141414; padding: 14px 20px; font-size: 19px; line-height: 1.6; max-width: 720px; font-weight: 600">{BLOG_TAGLINE}</p>\n'
            f'</div>\n</section>')
    if posts:
        listing = "\n".join(card(p) for p in posts)
    else:
        listing = ('<div style="background: #FFFFFF; border: 4px solid #141414; box-shadow: 8px 8px 0 #141414; padding: 28px; text-align: center">'
                   f'<p style="margin: 0; font-family: {B}; font-size: 32px; letter-spacing: 1px">FIRST POST COMING SOON</p></div>')
    index_main = (hero + '\n<section style="background: #FFF8E7; border-bottom: 4px solid #141414">\n'
                  '<div style="max-width: 860px; margin: 0 auto; padding: 64px 24px; display: flex; flex-direction: column; gap: 28px">\n'
                  + listing + '\n</div>\n</section>')
    (ROOT / "blog.html").write_text(page(head, tail, f"{BLOG_NAME} · Cort Craven, LLPC", BLOG_TAGLINE, BASE_URL + "blog.html", index_main), encoding="utf-8")

    # remove pages for posts that no longer exist
    keep = {f"blog-{p['slug']}.html" for p in posts}
    for old in ROOT.glob("blog-*.html"):
        if old.name not in keep:
            old.unlink()

    for p in posts:
        post_main = (f'<section class="ht-yellow" style="border-bottom: 4px solid #141414">\n'
                     f'<div style="max-width: 860px; margin: 0 auto; padding: 56px 24px; display: flex; flex-direction: column; align-items: flex-start; gap: 16px">\n'
                     f'<a href="blog.html" style="font-weight: 900; font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px; color: #141414; min-height: 44px; display: flex; align-items: center">← All posts</a>\n'
                     f'<span style="background: #FFF8E7; border: 3px solid #141414; padding: 6px 12px; font-weight: 900; font-size: 13px; letter-spacing: 2px">{BLOG_NAME.upper()} • {nice_date(p["date_obj"]).upper()}</span>\n'
                     f'<h1 style="margin: 0; background: #FFF8E7; border: 5px solid #141414; box-shadow: 10px 10px 0 #141414; padding: 14px 26px; font-family: {B}; font-weight: 400; font-size: clamp(36px, 5vw, 60px); line-height: 1.05; letter-spacing: 1.5px">{html.escape(p["title"])}</h1>\n'
                     f'</div>\n</section>\n'
                     f'<section style="background: #FFF8E7; border-bottom: 4px solid #141414">\n'
                     f'<article class="post-body" style="max-width: 760px; margin: 0 auto; padding: 56px 24px 72px">\n{p["html"]}\n'
                     f'<p style="margin-top: 40px"><a href="blog.html">← Back to all posts</a></p>\n</article>\n</section>')
        (ROOT / f"blog-{p['slug']}.html").write_text(
            page(head, tail, f"{p['title']} · {BLOG_NAME}", p["summary"], BASE_URL + f"blog-{p['slug']}.html", post_main), encoding="utf-8")

    # latest posts box on resources.html
    res = (ROOT / "resources.html").read_text(encoding="utf-8")
    latest = "\n".join(card(p, heading="h3") for p in posts[:2]) if posts else \
        '<p style="margin: 0; font-size: 18px; font-weight: 700">First post coming soon.</p>'
    res, n = re.subn(r"<!-- BLOG:START -->.*?<!-- BLOG:END -->",
                    lambda m: "<!-- BLOG:START -->\n" + latest + "\n<!-- BLOG:END -->", res, flags=re.S)
    if n != 1:
        raise SystemExit("resources.html: BLOG markers not found")
    (ROOT / "resources.html").write_text(res, encoding="utf-8")
    print(f"Built {len(posts)} post(s).")


if __name__ == "__main__":
    main()
