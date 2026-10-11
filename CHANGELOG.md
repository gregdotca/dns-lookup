# Changelog

## 2026-10-11

### Build Tailwind and daisyUI locally

- The page loaded Tailwind (the in-browser `@tailwindcss/browser` compiler) and daisyUI from jsDelivr on every visit. The CSS is now built at Docker build time instead, so the page no longer depends on a CDN or compiles CSS in the browser.
- `services/web/Dockerfile`: the builder stage downloads the Tailwind standalone CLI v4.3.3 (SHA-256 checked per architecture) and builds `project/assets/app.css`, which the final stage copies in.
- `services/web/project/styles/app.css`: new Tailwind input file, scanning only the templates.
- `services/web/project/styles/daisyui-5.7.46.mjs`: vendored daisyUI plugin (checked against the release's SHA-256), with only the `bumblebee` theme enabled.
- `services/web/project/templates/home.html`: replaced the CDN tags with a link to the built `app.css`.
- `.gitignore`: ignore the generated `app.css`.
- Added `CLAUDE.md` and this changelog.
