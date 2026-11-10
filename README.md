# Cort Craven, LLPC

Personal clinician website. Static HTML, hosted on GitHub Pages.

## Before launch
- Contact: email and text links only (no form). The email address is assembled by script on contact.html so it never appears in the page source.
- Fill every `[BRACKETED]` placeholder (license number, supervisor, address, rates, links).
- Remove `<meta name="robots" content="noindex, nofollow">` from every page so search engines can list the site.
- Remove the "Coming February 2027" banner at the top of each page once the LLPC is active.

- After connecting a custom domain, replace `https://notcraven.github.io/cort-site/` in the `og:` tags on every page so link previews keep working.

## Pages
`index.html` · `about.html` · `services.html` · `resources.html` · `contact.html`

## Accessible Practice blog
Posts are Markdown files in `posts/` with front matter (`title`, `date` YYYY-MM-DD, `summary`). Run `python3 scripts/build_blog.py` to regenerate `blog.html`, each `blog-<slug>.html`, and the latest-posts box on `resources.html`. Page chrome is copied from `resources.html`.
