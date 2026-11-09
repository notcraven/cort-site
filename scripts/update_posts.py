"""Pull the three newest Game World Therapy posts into resources.html.

Runs in GitHub Actions (see .github/workflows/update-posts.yml).
Replaces everything between the POSTS:START and POSTS:END markers.
If the feed can't be read, the page is left unchanged.
"""
import html, re, sys, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

FEED = "https://game-world-therapy.ghost.io/rss/"
PAGE = "resources.html"
COUNT = 3

CARD = ('<a href="{link}" style="background: #FFFFFF; border: 4px solid #141414; box-shadow: 6px 6px 0 #141414; '
        'padding: 18px 20px; text-decoration: none; color: #141414; display: flex; flex-direction: column; gap: 6px" '
        'target="_blank" rel="noopener">'
        '<span style="font-weight: 900; font-size: 19px">{title}</span>'
        '{date}'
        '<span style="font-size: 15px; line-height: 1.5">{summary}</span>'
        '<span class="sr-only"> (opens in a new tab)</span></a>')
DATE = '<span style="font-size: 13px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: #4A4A4A">{}</span>'


def clean(text, limit=None):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    if limit and len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
    return html.escape(text)


def main():
    try:
        req = urllib.request.Request(FEED, headers={"User-Agent": "cort-site-post-updater"})
        with urllib.request.urlopen(req, timeout=30) as r:
            root = ET.fromstring(r.read())
    except Exception as e:
        print(f"Feed unavailable, leaving page as is: {e}")
        return 0

    cards = []
    for item in root.iter("item"):
        title = clean(item.findtext("title"))
        link = (item.findtext("link") or "").strip()
        if not title or not link.startswith("https://"):
            continue
        date = ""
        try:
            d = parsedate_to_datetime(item.findtext("pubDate"))
            date = DATE.format(f"{d:%b} {d.day}, {d.year}")
        except Exception:
            pass
        summary = clean(item.findtext("description"), limit=150)
        cards.append(CARD.format(link=html.escape(link, quote=True), title=title, date=date, summary=summary))
        if len(cards) == COUNT:
            break

    if not cards:
        print("No posts found, leaving page as is.")
        return 0

    page = open(PAGE, encoding="utf-8").read()
    new = re.sub(r"(<!-- POSTS:START -->\n).*?(\n<!-- POSTS:END -->)",
                 lambda m: m.group(1) + "\n".join(cards) + m.group(2), page, flags=re.S)
    if new == page:
        print("No change.")
    else:
        open(PAGE, "w", encoding="utf-8").write(new)
        print(f"Updated {len(cards)} posts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
