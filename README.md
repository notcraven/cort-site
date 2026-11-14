# Cort Craven, LLPC

Personal clinician website. Static HTML, hosted on GitHub Pages.

## Before launch
- Contact: email and text links only (no form). The email address is assembled by script on contact.html so it never appears in the page source.
- Fill every `[BRACKETED]` placeholder (license number, supervisor, address, rates, links).
- Remove `<meta name="robots" content="noindex, nofollow">` from every page so search engines can list the site.
- Remove the "Coming February 2027" banner at the top of each page once the LLPC is active.

- The site runs on https://creativemodecounseling.com (CNAME file in the repo root). The `og:` tags and BASE_URL in scripts/build_blog.py use that address.

## Pages
`index.html` · `about.html` · `services.html` · `resources.html` · `contact.html`

## Accessible Practice blog
Posts are Markdown files in `posts/` with front matter (`title`, `date` YYYY-MM-DD, `summary`). Run `python3 scripts/build_blog.py` to regenerate `blog.html`, each `blog-<slug>.html`, and the latest-posts box on `resources.html`. Page chrome is copied from `resources.html`.

## Specialty pages

Each specialty has its own page, built from a Markdown file in `specialties/`:
individual-therapy, gender-affirming-therapy, neurodivergent-affirming-therapy,
chronic-illness-therapy, rebuilding-trust-after-harm. (Game-informed therapy
keeps its own hand-built page, game-informed-therapy.html.)

To edit one, change its `.md` file and run `python3 scripts/build_specialties.py`.
The file format is described at the top of that script. The page header, nav and
footer are copied from game-informed-therapy.html, so rebuild after changing the nav.
