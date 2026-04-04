---
name: Email Template Design State
description: Current state and design decisions for the morning-brief email HTML/text templates
type: project
---

The email templates were redesigned in April 2026 (commit ef57484, merged into development via 1a3a83d).

Key design decisions made:
- Full table-based layout replacing div-based layout for Outlook compatibility
- Dark terminal aesthetic preserved: #050a05 background, #a3e635 lime accent, #d1fae5 body text
- Topic labels styled as pill-badges using background-color + border on a `<td>` (no border-radius, Outlook-safe)
- Deep Dive section has a 4px wide left accent bar (`<td style="background-color: #a3e635; width: 4px">`)
- "Read Full Article" uses outlined button via table border, not a div or anchor styled as button
- Footer text contrast raised from #2d4a2d to #4a7a4a
- MSO Office namespaces and PixelsPerInch setting added for Outlook rendering
- Hidden preheader div added for inbox preview text
- Spacer rows use explicit height `<td>` cells, not margin

**Why:** Original template used div-based layout and margin-based spacing which breaks in Outlook. No preheader text meant poor inbox preview UX.

**How to apply:** Keep table-based structure for any future layout changes. Never use border-radius, flexbox, grid, or margin for spacing in the HTML template. Spacers via `<td style="height: Xpx">` rows only.
