"""Build one page per specialty from specialties/*.md.

Each file starts with front matter (title, h1, order, hero, tagline,
description, card, cta), then sections:

    ## Heading                      plain text section (a "> quote" becomes a yellow callout)
    ## [aside] Heading              purple side panel next to the section above it
    ## [cards] Heading              "- **Title** text" items shown as cards
    ## [checks] Heading             "- item" shown as a checklist
    ## [faq] Heading                "### Question" followed by the answer

Run:  python3 scripts/build_specialties.py
Writes <slug>.html for each file. The page chrome (header, nav, footer)
is copied from game-informed-therapy.html so it always matches the site.
Game-informed therapy keeps its own hand-built page and is listed in the
"other ways I can help" links.
"""
import html
import pathlib
import re

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "specialties"
BASE_URL = "https://creativemodecounseling.com/"
B = "'Bangers', Impact, 'Arial Narrow', sans-serif"
CARD_COLORS = [("#FF4FA3", "#141414"), ("#FFD83B", "#141414"), ("#7B4AE2", "#FFF8E7"), ("#19B8C9", "#141414")]
GAME = {"slug": "game-informed-therapy", "h1": "Game-Informed Therapy", "order": 4,
        "card": "Using the games you love as a shared language for change."}
ARROW = ('<svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
         'stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"></path></svg>')
CHECK = ('<svg aria-hidden="true" focusable="false" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#141414" '
         'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l5 5 9-10"></path></svg>')
H2 = f"margin: 0; font-family: {B}; font-weight: 400; font-size: clamp(34px, 4vw, 52px); letter-spacing: 1.5px; font-style: italic"
H2_BOX = ("margin: 0; align-self: center; background: #FFF8E7; border: 4px solid #141414; box-shadow: 6px 6px 0 #141414; "
          f"padding: 10px 28px; font-family: {B}; font-weight: 400; font-size: clamp(34px, 4vw, 48px); letter-spacing: 1.5px; font-style: italic; text-align: center")
E = lambda s: html.escape(s, quote=True)


def inline(md):
    """Markdown for one line or paragraph, without the wrapping <p>."""
    out = markdown.markdown(md, extensions=["smarty"]).strip()
    out = re.sub(r"^<p>(.*)</p>$", r"\1", out, flags=re.S)
    return re.sub(r'<a href="(https?://[^"]+)">(.*?)</a>',
                  r'<a href="\1" target="_blank" rel="noopener">\2<span class="sr-only"> (opens in a new tab)</span></a>', out)


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        raise SystemExit(f"{path.name}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    for k in ("title", "h1", "tagline", "description", "card"):
        if not meta.get(k):
            raise SystemExit(f"{path.name}: front matter needs '{k}'")
    meta["slug"] = path.stem
    meta["order"] = int(meta.get("order", 99))
    sections = []
    for block in re.split(r"^## ", m.group(2), flags=re.M)[1:]:
        head, _, body = block.partition("\n")
        kind = "text"
        km = re.match(r"\[(\w+)\]\s*(.*)", head.strip())
        if km:
            kind, head = km.group(1), km.group(2)
        sections.append({"kind": kind, "heading": head.strip(), "body": body.strip()})
    meta["sections"] = sections
    return meta


def items(body):
    return [l[2:].strip() for l in body.splitlines() if l.startswith("- ")]


def text_html(body):
    out = []
    for para in re.split(r"\n\s*\n", body):
        para = para.strip()
        if not para:
            continue
        if para.startswith(">"):
            q = " ".join(l.lstrip("> ").strip() for l in para.splitlines())
            out.append(f'<p style="margin: 0; font-size: 19px; line-height: 1.65; background: #FFD83B; border: 3px solid #141414; '
                       f'box-shadow: 5px 5px 0 #141414; padding: 16px 20px; font-weight: 700">{inline(q)}</p>')
        else:
            out.append(f'<p style="margin: 0; font-size: 19px; line-height: 1.65">{inline(para)}</p>')
    return "\n".join(out)


def render_text(sec, aside=None):
    left = (f'<div style="flex: 1.3 1 460px; min-width: 0; display: flex; flex-direction: column; gap: 20px">\n'
            f'<h2 style="{H2}">{E(sec["heading"].upper())}</h2>\n{text_html(sec["body"])}\n</div>')
    right = ""
    if aside:
        lines = "\n".join(f'<p style="margin: 0; font-size: 18px; line-height: 1.6">{inline(i)}</p>' for i in items(aside["body"]))
        right = (f'\n<div style="flex: 1 1 320px; min-width: 0; background: #7B4AE2; color: #FFF8E7; border: 4px solid #141414; '
                 f'box-shadow: 8px 8px 0 #141414; padding: 28px; display: flex; flex-direction: column; gap: 16px; transform: rotate(1deg)">\n'
                 f'<h2 style="margin: 0; font-family: {B}; font-weight: 400; font-size: 30px; letter-spacing: 1px; line-height: 1.1">{E(aside["heading"].upper())}…</h2>\n{lines}\n</div>')
    return (f'<section style="background: #FFF8E7; border-bottom: 4px solid #141414">\n'
            f'<div style="max-width: 1180px; margin: 0 auto; padding: 80px 24px; display: flex; flex-wrap: wrap; align-items: flex-start; gap: 48px">\n'
            f'{left}{right}\n</div>\n</section>')


def render_cards(sec):
    cards = []
    for n, it in enumerate(items(sec["body"])):
        m = re.match(r"\*\*(.+?)\*\*\s*(.*)", it)
        title, desc = (m.group(1), m.group(2)) if m else (it, "")
        bg, fg = CARD_COLORS[n % len(CARD_COLORS)]
        cards.append(f'<article style="background: #FFFFFF; border: 4px solid #141414; box-shadow: 8px 8px 0 #141414">'
                     f'<h3 style="margin: 0; background: {bg}; color: {fg}; border-bottom: 4px solid #141414; padding: 14px 20px; '
                     f'font-family: {B}; font-weight: 400; font-size: 26px; letter-spacing: 1px">{E(title.upper())}</h3>'
                     f'<p style="margin: 0; padding: 20px; font-size: 17px; line-height: 1.6">{inline(desc)}</p></article>')
    return (f'<section class="ht-teal" style="border-bottom: 4px solid #141414">\n'
            f'<div style="max-width: 1280px; margin: 0 auto; padding: 80px 24px; display: flex; flex-direction: column; gap: 40px">\n'
            f'<h2 style="{H2_BOX}">{E(sec["heading"].upper())}</h2>\n'
            f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); gap: 28px">\n'
            + "\n".join(cards) + "\n</div>\n</div>\n</section>")


def render_checks(sec):
    dots = ["#19B8C9", "#FF4FA3", "#FFD83B", "#7B4AE2"]
    rows = []
    for n, it in enumerate(items(sec["body"])):
        rows.append(f'<li style="display: flex; gap: 16px; align-items: flex-start; background: #FFFFFF; border: 3px solid #141414; '
                    f'box-shadow: 5px 5px 0 #141414; padding: 22px"><span aria-hidden="true" style="flex: none; width: 40px; height: 40px; '
                    f'border-radius: 50%; background: {dots[n % 4]}; border: 3px solid #141414; display: flex; align-items: center; '
                    f'justify-content: center">{CHECK}</span><span style="font-size: 18px; line-height: 1.5; font-weight: 600">{inline(it)}</span></li>')
    return (f'<section style="background: #FFF8E7; border-bottom: 4px solid #141414">\n'
            f'<div style="max-width: 1180px; margin: 0 auto; padding: 80px 24px; display: flex; flex-direction: column; gap: 40px">\n'
            f'<h2 style="{H2}; text-align: center">{E(sec["heading"].upper())}</h2>\n'
            f'<ul style="list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 440px), 1fr)); gap: 22px">\n'
            + "\n".join(rows) + "\n</ul>\n</div>\n</section>")


def render_faq(sec):
    qs = re.split(r"^### ", sec["body"], flags=re.M)[1:]
    dots = ["#19B8C9", "#FFD83B", "#FF4FA3"]
    out = []
    for n, q in enumerate(qs):
        question, _, answer = q.partition("\n")
        paras = [p.strip() for p in re.split(r"\n\s*\n", answer.strip()) if p.strip()]
        body = "\n".join(f'<p style="margin: 0; padding: 0 22px {22 if i == len(paras) - 1 else 14}px; font-size: 17px; line-height: 1.65">{inline(p)}</p>'
                         for i, p in enumerate(paras))
        out.append(f'<details{" open" if n == 0 else ""} style="background: #FFFFFF; border: 4px solid #141414; box-shadow: 5px 5px 0 #141414">\n'
                   f'<summary class="faq-btn"><span>{E(question.strip())}</span><span aria-hidden="true" class="faq-sign" style="flex: none; '
                   f'width: 36px; height: 36px; border-radius: 50%; border: 3px solid #141414; background: {dots[n % 3]}; display: flex; '
                   f'align-items: center; justify-content: center; font-weight: 900; font-size: 22px; line-height: 1"></span></summary>\n{body}\n</details>')
    return (f'<section class="ht-purple" style="border-bottom: 4px solid #141414">\n'
            f'<div style="max-width: 920px; margin: 0 auto; padding: 80px 24px; display: flex; flex-direction: column; gap: 32px">\n'
            f'<h2 style="{H2_BOX}">{E(sec["heading"].upper())}</h2>\n'
            f'<div style="display: flex; flex-direction: column; gap: 16px">\n' + "\n".join(out) + "\n</div>\n</div>\n</section>")


def render_related(page, all_pages):
    links = []
    for p in sorted(all_pages, key=lambda p: p["order"]):
        if p["slug"] == page["slug"]:
            continue
        links.append(f'<li><a href="{p["slug"]}.html" style="display: flex; flex-direction: column; gap: 6px; height: 100%; box-sizing: border-box; '
                     f'background: #FFFFFF; border: 3px solid #141414; box-shadow: 5px 5px 0 #141414; padding: 18px 20px; color: #141414; '
                     f'text-decoration: none"><span style="font-family: {B}; font-size: 24px; letter-spacing: 1px; line-height: 1.1">'
                     f'{E(p["h1"].upper())} →</span><span style="font-size: 16px; line-height: 1.5">{E(p["card"])}</span></a></li>')
    return (f'<section style="background: #FFF8E7; border-bottom: 4px solid #141414">\n'
            f'<div style="max-width: 1180px; margin: 0 auto; padding: 72px 24px; display: flex; flex-direction: column; gap: 32px">\n'
            f'<h2 style="{H2}; text-align: center">OTHER WAYS I CAN HELP</h2>\n'
            f'<ul style="list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); gap: 22px">\n'
            + "\n".join(links) + '\n</ul>\n'
            f'<a href="services.html" style="align-self: center; font-weight: 900; font-size: 16px; text-transform: uppercase; letter-spacing: 0.5px; '
            f'min-height: 44px; display: flex; align-items: center; color: #141414">See all services and fees →</a>\n</div>\n</section>')


def render_page(p, all_pages):
    hero = (f'<section class="{p.get("hero", "ht-teal")}" style="border-bottom: 4px solid #141414">\n'
            f'<div style="max-width: 1080px; margin: 0 auto; padding: 56px 24px 72px; display: flex; flex-direction: column; align-items: center; gap: 22px; text-align: center">\n'
            f'<a href="services.html" style="align-self: flex-start; font-weight: 900; font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px; '
            f'color: #141414; min-height: 44px; display: flex; align-items: center; background: #FFF8E7; border: 3px solid #141414; padding: 0 14px">← All services</a>\n'
            f'<h1 style="margin: 0; background: #FFF8E7; border: 5px solid #141414; box-shadow: 10px 10px 0 #141414; padding: 14px clamp(14px, 3vw, 32px); font-family: {B}; '
            f'font-weight: 400; font-size: clamp(32px, 6vw, 72px); line-height: 1; letter-spacing: 1px; overflow-wrap: anywhere; max-width: 100%; box-sizing: border-box; transform: rotate(-1.5deg)">{E(p["h1"].upper())}</h1>\n'
            f'<p style="margin: 0; background: #FFF8E7; border: 3px solid #141414; padding: 16px 22px; font-size: 20px; line-height: 1.55; max-width: 720px; font-weight: 600">{inline(p["tagline"])}</p>\n'
            f'</div>\n</section>')
    parts, secs, i = [hero], p["sections"], 0
    while i < len(secs):
        s = secs[i]
        if s["kind"] == "text":
            aside = secs[i + 1] if i + 1 < len(secs) and secs[i + 1]["kind"] == "aside" else None
            parts.append(render_text(s, aside))
            i += 2 if aside else 1
            continue
        parts.append({"cards": render_cards, "checks": render_checks, "faq": render_faq}.get(s["kind"], render_text)(s))
        i += 1
    parts.append(render_related(p, all_pages))
    parts.append(f'<section class="ht-pink" style="border-bottom: 4px solid #141414">\n'
                 f'<div style="max-width: 1080px; margin: 0 auto; padding: 64px 24px; display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 28px; text-align: center">\n'
                 f'<h2 style="margin: 0; font-family: {B}; font-weight: 400; font-size: clamp(36px, 4.4vw, 58px); letter-spacing: 1.5px">{E(p.get("cta", "Ready to start?").upper())}</h2>\n'
                 f'<a href="contact.html" style="min-height: 52px; box-sizing: border-box; display: inline-flex; align-items: center; gap: 10px; padding: 0 24px; '
                 f'background: #FFD83B; color: #141414; text-decoration: none; font-weight: 900; font-size: 18px; letter-spacing: 0.5px; border: 4px solid #141414; '
                 f'box-shadow: 6px 6px 0 #141414; text-transform: uppercase">Book a free consult {ARROW}</a>\n</div>\n</section>')
    return "\n\n".join(parts)


def chrome():
    page = (ROOT / "game-informed-therapy.html").read_text(encoding="utf-8")
    head, rest = page.split('<main id="main"', 1)
    return head, rest.split("</main>", 1)[1]


def wrap(head, tail, p, main):
    title = f'{p["title"]} · Creative Mode Counseling'
    url = BASE_URL + p["slug"] + ".html"
    h = re.sub(r"<title>.*?</title>", f"<title>{E(title)}</title>", head, count=1)
    h = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{E(p["description"])}">', h, count=1)
    h = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{E(title)}">', h, count=1)
    h = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{E(p["description"])}">', h, count=1)
    h = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', h, count=1)
    h = re.sub(r'<link rel="canonical" href="[^"]*">\n?', "", h)
    h = h.replace("</title>", f'</title>\n<link rel="canonical" href="{url}">', 1)
    # nav: highlight Services (this page is part of it) instead of Game-Informed Therapy
    plain = "border: 3px solid transparent\">"
    hot = "background: #19B8C9; border: 3px solid #141414\">"
    h = h.replace('<a href="game-informed-therapy.html" aria-current="page" style="min-height: 44px; box-sizing: border-box; display: flex; align-items: center; padding: 0 16px; font-weight: 800; font-size: 17px; text-decoration: none; color: #141414; ' + hot,
                  '<a href="game-informed-therapy.html" style="min-height: 44px; box-sizing: border-box; display: flex; align-items: center; padding: 0 16px; font-weight: 800; font-size: 17px; text-decoration: none; color: #141414; ' + plain, 1)
    h = h.replace('<a href="services.html" style="min-height: 44px; box-sizing: border-box; display: flex; align-items: center; padding: 0 16px; font-weight: 800; font-size: 17px; text-decoration: none; color: #141414; ' + plain,
                  '<a href="services.html" aria-current="true" style="min-height: 44px; box-sizing: border-box; display: flex; align-items: center; padding: 0 16px; font-weight: 800; font-size: 17px; text-decoration: none; color: #141414; ' + hot, 1)
    return h + '<main id="main" tabindex="-1" style="outline: none">\n' + main + "\n</main>" + tail


def main():
    pages = [parse(f) for f in sorted(SRC.glob("*.md"))]
    head, tail = chrome()
    for p in pages:
        (ROOT / f'{p["slug"]}.html').write_text(wrap(head, tail, p, render_page(p, pages + [GAME])), encoding="utf-8")
    print(f"Built {len(pages)} specialty page(s): " + ", ".join(p["slug"] for p in pages))


if __name__ == "__main__":
    main()
