# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

DNS Lookup is a single-page Flask app that reports DNS details for a domain (A, PTR, NS, MX, TXT, `www.`/`mail.` A records) and checks A-record propagation against a fixed list of public resolvers around the world. Live demo: https://dnscheck.greg.ca

## Commands

Production (gunicorn, port 8086 on the host, container name `dnscheck`):

```sh
docker-compose up -d --build
```

Local development without Docker (from `services/web/`, using the repo's `.venv` and the Tailwind standalone CLI to build the CSS):

```sh
pip install -r requirements.txt
tailwindcss -i project/styles/app.css -o project/assets/app.css --watch &
FLASK_APP=project/__init__.py python manage.py run -h 0.0.0.0
```

Lint (the production Docker build runs this and fails on errors):

```sh
cd services/web && flake8 --ignore=E501,W503,F401,E126 .
```

There are no tests.

### DEV/PROD environment swap

The dev config files are local-only (listed in `.git/info/exclude`, not tracked): `docker-compose.DEV.yml`, `services/web/Dockerfile.DEV`, `to-dev.sh`, and `to-prod.sh`. `./to-dev.sh` renames the tracked PROD `docker-compose.yml` and `services/web/Dockerfile` to `*.PROD` and moves the DEV versions into their place (Flask dev server on port 5000, source bind-mounted into `/app`, with `tailwindcss --watch=always` rebuilding `project/assets/app.css` alongside it; the generated file on the host is root-owned); `./to-prod.sh` swaps back. Check which environment is active (`ls docker-compose.*.yml`) before editing either file, and **always switch back to PROD before committing**, or the tracked files will show as deleted/modified with dev content.

## Architecture

All application logic lives in `services/web/project/__init__.py`; `services/web/manage.py` wraps it in a `FlaskGroup` and is the gunicorn entry point (`manage:app`).

- `GET /` renders the empty form; `POST /` redirects to `/<domain>`; `GET /<domain>` runs the lookup.
- `get_details()` does every lookup (via `socket` and `dnspython`), returning a positional list; each failure is swallowed and replaced with `*MISSING*`. `process_domain()` unpacks that list by index, so the order of its return values matters.
- `get_propagation()` queries each resolver in the `dig_servers` dict and marks results green/red against the system resolver's IP.
- Results are built as raw HTML strings and **appended after** the rendered `home.html` (i.e. after `</html>`). The template's `{{ page_body|safe }}` is never passed. Values are colour-coded (`var(--result-green)`/`var(--result-red)`, defined in `app.css`) with `highlight_text()`/`get_colour()` against hard-coded "expected" values (e.g. MX `10 mail.<domain>`, SPF `"v=spf1 mx a -all"`). Domain input and DNS answers are concatenated into the HTML unescaped.
- Static files are served from `project/assets/` at `/assets/...` (Flask's `static_folder`; use `url_for('static', ...)`). jQuery and the favicon are vendored there. `home.html` optionally includes `templates/custom.headers` (gitignored), which is used for site-specific extra `<head>` content like analytics.
- **CSS build:** Tailwind 4 and daisyUI 5 are built at Docker build time, not loaded from a CDN. The Tailwind standalone CLI (version and per-architecture SHA-256s pinned as `ARG`s in the Dockerfile builder stage, and in `Dockerfile.DEV`) compiles `project/styles/app.css` into `project/assets/app.css` (gitignored), scanning only `project/templates/`. daisyUI is the vendored plugin `project/styles/daisyui-<version>.mjs`. To upgrade, update the `ARG`s, or replace the `.mjs` file and its reference in `app.css`. A class used only from Python (like the results HTML) won't be in the build unless it also appears in a template; the results use inline styles, so they're unaffected.
- **Dark mode:** automatic only, with no toggle, JavaScript, or `data-theme` attribute. `bumblebee --default, business --prefersdark` in `project/styles/app.css` puts `business` inside `@media (prefers-color-scheme: dark)` on `:root:not([data-theme])`, so adding `data-theme` to `<html>` would lock the page to one theme. A `color-scheme` meta tag in `home.html` tells the browser about both modes before the CSS loads. Use daisyUI theme colours (`base-content`, `base-200`, and so on), not hard-coded colour classes, so both modes keep working. Tailwind's `dark:` variant uses the same media query, so per-mode tweaks go there (the Lookup button is `btn-accent dark:btn-primary`). Unlayered rules at the end of `app.css` beat daisyUI's layered theme: they set a darker `--color-primary` and `bumblebee`'s `--radius-*` values in dark mode, plus the `--result-green`/`--result-red` colours (one pair per mode) that `highlight_text()` uses for the results.

`requirements.txt` still lists `Flask-SQLAlchemy` and `psycopg2-binary`, but the app has no database. The base image is Python 3.9.
