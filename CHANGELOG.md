# Changelog

## 2026-10-11

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
