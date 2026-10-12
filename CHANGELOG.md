# Changelog

## 2026-10-11

### Escape results, speed up lookups, update Python

- Fix one slow DNS server blocking the whole site. gunicorn ran a single sync worker, and the propagation check waited up to dnspython's default 5 seconds for each resolver that didn't answer, so a lookup with a dead resolver made every other visitor wait behind it. gunicorn now runs 4 workers, and each propagation resolver gets 2 seconds (tested: an unreachable resolver now fails after 2.1 seconds, and 4 simultaneous lookups all finished in about 0.8 seconds).
  - `docker-compose.yml:10`: add `--workers 4` to the gunicorn command.
  - `services/web/project/__init__.py`: set `resolver.lifetime = 2` in `get_propagation()`.
- Fix reflected XSS in the results. The domain from the URL and every DNS answer (A, PTR, NS, MX, TXT) were concatenated into the results HTML unescaped, so a link like `/<img src=x onerror=...>` ran script on the page. They're now escaped with `markupsafe.escape`, so that link shows the text instead.
  - `services/web/project/__init__.py`: `process_domain()` escapes the domain, the IP address, and the nameservers. `highlight_text()` escapes the text it's given, which covers every other value. The colour comparisons still use the raw values, so results are coloured as before.
- Fix an open redirect. `POST /` redirected to `"/" + domain`, so a domain of `/evil.com` produced `Location: //evil.com`, a protocol-relative link to another site. The domain is now URL-quoted with `safe=""` (so `/` becomes `%2F`), and that request returns a 404 instead (tested).
- Update Python from 3.9 to 3.14, Flask from 2.3.0 to 3.1.3, Werkzeug from 2.3.0 to 3.1.9, gunicorn from 20.1.0 to 26.2.0, and flake8 from 3.9.1 to 7.4.1, matching the dig project. Python 3.9 reached end of life in October 2025, so it no longer gets security fixes. The other upgrades came with it: Werkzeug 2.3.0 uses `ast.Str`, which Python 3.12 removed, so the site crashed on start; gunicorn 20.1.0 has a request-smuggling vulnerability (CVE-2024-1135, fixed in 22.0.0); and flake8 3.9 misreads newer Python syntax. gunicorn 26 also adds a control socket that it tried to create in `/home/app/.gunicorn`, which the `app` user can't write to, logging a `Permission denied` error on every start, so it's turned off with `--no-control-socket`.
  - `services/web/Dockerfile`: `python:3.14.7-slim` in both stages, flake8 7.4.1, and `AS builder` in capitals (Docker warns about the lowercase form).
  - `services/web/requirements.txt`: new versions, and the commented-out old pins removed.
  - `docker-compose.yml:10`: add `--no-control-socket` to the gunicorn command.
- Remove `Flask-SQLAlchemy` and `psycopg2-binary` from `services/web/requirements.txt`. The app has no database and never imported either one.
- `CLAUDE.md`: document the escaping, the redirect quoting, the Python version, the gunicorn workers, and the control socket setting.

### Add AI Code Rating, update copyright and README

- `ACR.md`: new [AI Code Rating](https://aicoderating.com/) file, rated B1b (Experienced maintainer, AI wrote 1–25% of the code, all of it read by the maintainer). `README.md` links to it with a badge under the title.
- `LICENSE`, `README.md`: copyright updated from `2024` to `2024-2026`, with the maintainer's email.
- `README.md`: the install step said to load `https://IP_ADDRESS:8086`, but gunicorn serves plain HTTP on that port, so the link now uses `http://`.

### Label the domain input for screen readers

- The domain input had only a `placeholder`, which isn't a reliable accessible name, so screen readers could announce it as an unlabelled text field.
- `services/web/project/templates/home.html`: added `aria-label="Domain"`, matching the placeholder. The Lookup button is already named by its text.

### Add automatic dark mode

- The page followed only the light `bumblebee` theme, locked in by `data-theme` on `<html>`. It now switches to the dark `business` theme when the browser or OS prefers dark mode, with no toggle or JavaScript.
- `services/web/project/styles/app.css`: enabled `business` as the `--prefersdark` theme. Dark mode gets a darker navy `--color-primary` for the Lookup button and `bumblebee`'s corner radii, so both modes have the same shape.
- `services/web/project/templates/home.html`: removed `data-theme="bumblebee"` (it would lock the page to one theme), added a `color-scheme` meta tag, and made the button `dark:btn-primary` instead of `business`'s orange accent.
- `services/web/project/__init__.py`: `highlight_text()` now colours results with `var(--result-green)`/`var(--result-red)` instead of fixed `green`/`red`. On the dark background (`#202020`), the fixed green would have been 3.17:1 and the fixed red (`#ff0000`) 4.07:1, and the red was already 4.00:1 on white, all under WCAG AA's 4.5:1. Each mode now has its own pair (light `#008000` 5.14:1 and `#cc0000` 5.89:1 on white; dark `#4ade80` 9.35:1 and `#f87171` 5.89:1 on `#202020`).
- `CLAUDE.md`: documented the dark mode setup.

### Build Tailwind and daisyUI locally

- The page loaded Tailwind (the in-browser `@tailwindcss/browser` compiler) and daisyUI from jsDelivr on every visit. The CSS is now built at Docker build time instead, so the page no longer depends on a CDN or compiles CSS in the browser.
- `services/web/Dockerfile`: the builder stage downloads the Tailwind standalone CLI v4.3.3 (SHA-256 checked per architecture) and builds `project/assets/app.css`, which the final stage copies in.
- `services/web/project/styles/app.css`: new Tailwind input file, scanning only the templates.
- `services/web/project/styles/daisyui-5.7.46.mjs`: vendored daisyUI plugin (checked against the release's SHA-256), with only the `bumblebee` theme enabled.
- `services/web/project/templates/home.html`: replaced the CDN tags with a link to the built `app.css`.
- `.gitignore`: ignore the generated `app.css`.
- Added `CLAUDE.md` and this changelog.
