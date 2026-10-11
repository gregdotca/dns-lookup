---
rating: B1b
spec: "0.1"
updated: 2026-10-11
---

# AI Code Rating

**ACR B1b** (Maintainer: Experienced · AI Share: 1–25% · Oversight: Reviewed)

This project is rated with [AI Code Rating](https://aicoderating.com/spec/0.1/), spec version 0.1.

## How AI Was Used

The maintainer wrote DNS Lookup by hand in 2024 and 2025: the Flask app, the DNS and propagation checks, the page template, and the Docker setup. In 2026 an AI coding agent added a step to the Docker build that compiles the page's CSS locally instead of loading it from a CDN, added automatic dark mode with result colours that stay readable in both modes, and labelled the form input for screen readers. The maintainer chose the changes and the look, and read all of the code the AI wrote.

The AI's changes are also reviewed by a second AI, and the two go back and forth until it doesn't find any more issues. That doesn't change the oversight level. Commits are marked with `Co-Authored-By: Claude Code` and, where Codex reviewed them, `Reviewed-By: Codex`.
