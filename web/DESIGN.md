# RivalLens design system (applied)

Source: `docs/design/design-reference.md` (provided reference). We use its **design language**, not its brand: no Mastercard name, logo, or red/yellow mark anywhere. Tokens live in `app/globals.css` (`@theme`). Shared pieces live in `components/ui.tsx`.

## Tokens
| Token | Value | Use |
|---|---|---|
| `canvas` | `#F3F0EE` | Page background (never pure white) |
| `lifted` | `#FCFBFA` | Panels laid on the canvas |
| `white` | `#FFFFFF` | Floating nav pill, evidence cards, badges |
| `ink` | `#141413` | Text, primary buttons, footer, "your business" circle |
| `charcoal` | `#262627` | Secondary body text |
| `slate` | `#696969` | Muted text (AA on canvas) |
| `dust` / `ghost` | `#D1CDC7` / `#E8E2DA` | Decorative only; "before" highlight; never body text |
| `signal` | `#CF4500` | **Meaningful change / high-priority alert only.** Our single aggressive colour |
| `signal-light` | `#F37338` | Orbit arcs, eyebrow dot, logo satellite, "after" highlight tint |
| `link` | `#3860BE` | Inline links |

**Radius:** `btn` 20px (buttons, small panels) · `stadium` 40px (cards, sections) · `pill` 999px (nav, badges, chips) · full circle (icon buttons, competitor marks). Nothing in the 8–16px range.
**Shadow:** `lift-1` (floating nav) · `lift-2` (evidence and raised cards). No hard shadows.
**Type:** Sofia Sans, variable, one family. Body 450; headings 500 with −2% tracking; H1 64/64 (40 on mobile), H2 36, H3 24/1.2; eyebrow 14/700 uppercase +4% with an orange dot, used only for section categories.

## Adaptations for an app (vs the marketing reference)
- **Signal orange** means "meaningful change" here. It's still used sparingly: the meaningful-change label, high-priority alerts, and the after highlight.
- **Density:** app screens use 32px section gaps instead of 96–128px; marketing spacing stays on the landing page.
- **Orbit motif** = competitors orbiting your business (landing hero only). Arcs are removed from data screens.
- **Labels:** "Sample data" / "Demo data" pill badges (`SampleBadge`) on every placeholder or simulated item.
- **Light theme only** (the reference defines none for dark).

## Rules
- Primary action = ink pill; secondary = white pill with ink outline. Use active voice ("Run monitor", "Open receipt").
- Errors say what happened and what to do next; empty screens invite the next action.
- Visible focus ring (2px ink), 44px minimum targets, `prefers-reduced-motion` stops the orbit drift.
