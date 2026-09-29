# UZQUANT Terminal Design System

## Purpose

The terminal is a dense, read-only research surface. The backend is authoritative; the browser formats and filters stored results but does not calculate valuations, factors, confidence, gates, or signals.

## Navigation

The persistent navigation is: **MARKET, SCREENER, RESEARCH, VALUATION, FACTORS, EVIDENCE, COVERAGE, SYSTEM**. MARKET summarizes observed activity. COVERAGE is the primary evidence-completeness view. SYSTEM keeps operational health separate from research conclusions.

## Visual language

| Token | Value | Use |
| --- | --- | --- |
| Background | `#0B1220` | terminal canvas and navigation rail |
| Surface | `#111827` | primary panels |
| Raised surface | `#162033` | controls and emphasized panels |
| Primary text | `#F4F1EA` | headings and values |
| Champagne | `#C6A15B` | active navigation, evidence links, focus |
| Emerald | `#4FAE86` | healthy/available |
| Amber | `#D2A64D` | partial, stale, low confidence |
| Crimson | `#C75B64` | failed, blocked, critical risk |
| Blue | `#648FC7` | neutral analytical emphasis |
| Slate | `#8F9BAD` | secondary text |

System sans-serif is used for prose. Identifiers, labels and numeric values use tabular numeral styling and a system monospace stack where appropriate.

## Data display rules

- Missing values render as `n/a`, never `0`, a dash that could imply zero, or an empty cell.
- A genuine observed zero remains `0` or `0.0%`.
- Common and preferred securities always have explicit class labels.
- Research states are classifications, not orders.
- Tables keep headers sticky and use horizontal scrolling for the complete market-wide schema.
- Status colors supplement text labels; color alone never carries meaning.
- Friendly errors state that no analytical fallback was manufactured.

## Interaction

The screener supports text filtering, class/state/valuation/liquidity filters, deterministic sorting, and the documented exploration views. Security, valuation and evidence pages use the same canonical ticker selector. Blocker rows expand to show a code, approved taxonomy and stored evidence reason.

## Responsive behavior

The desktop terminal is optimized for dense tables. Below 1200 pixels, metric cards and split panels collapse to fewer columns while wide analytical tables retain horizontal scrolling so fields are not silently removed.
