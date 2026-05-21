# Design references

Drop visual references here for Claude / the `ui-ux-pro-max` skill to read.

## Folder layout

```
design-refs/
├─ screenshots/   # UIs you like (PNG, JPG, WebP) — competitor dashboards, dribbble shots
├─ logos/         # Brand marks, university/team logos (SVG preferred, PNG fine)
├─ svgs/          # SVG illustrations / icons to embed verbatim in the app
├─ palettes/      # color-palette images or CSS files
└─ notes.md       # free-form notes: "I want the navbar to look like screenshots/foo.png"
```

## How Claude uses these

- Image files (PNG, JPG, SVG, WebP) — Claude reads them directly via the `Read` tool and can describe what it sees in detail.
- `notes.md` — Claude reads it like a brief. Reference filenames inline:
  `the verdict card should feel like screenshots/dribbble-1.png — same depth + glow`
- The `ui-ux-pro-max` skill itself is **not** asset-aware — it's a CSV database of styles, palettes, fonts. So putting files here helps Claude, not the skill.

## Quick adds

- Paste URLs in chat (Figma share links, Dribbble pages, Behance, brand sites) — Claude can `WebFetch` them.
- The persisted design system lives at `frontend/design-system/anomalydetector/MASTER.md`. To override rules for a specific page, add `frontend/design-system/anomalydetector/pages/<page-name>.md`.
