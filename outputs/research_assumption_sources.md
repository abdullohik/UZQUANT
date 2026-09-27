# Research Assumption Sources

All inputs below are stored by scenario, source, source date, methodology,
provenance class, confidence, and assumption version
`ipky-residual-income/1.0.0`.

| Input | Value | Classification | Source / date | Treatment |
|---|---:|---|---|---|
| CBU 10-year zero rate | 16.96054015902% | OBSERVED / AUTHORITATIVE_SOURCE | CBU curve, 2026-09-23 | continuous nominal UZS government rate; not WACC |
| Effective government rate | 18.4837224179% | SOURCE_DERIVED | CBU curve | `exp(continuous rate)-1` |
| Uzbekistan default spread | 3.06% | AUTHORITATIVE_RESEARCH_INPUT | Damodaran, 2026-01-05 | removed from government yield before equity additions |
| Mature-market ERP | 4.23% | AUTHORITATIVE_RESEARCH_INPUT | Damodaran, 2026-01-05 | multiplied by beta |
| Uzbekistan CRP | 4.66% | AUTHORITATIVE_RESEARCH_INPUT | Damodaran, 2026-01-05 | explicit country-risk input |
| Regional-bank beta | 0.51 | AUTHORITATIVE_RESEARCH_INPUT | Damodaran Global Betas, 2026-01 | 825-firm regional-bank category |
| Base cost of equity | 22.2410224179% | MODEL_ESTIMATED | formula from sourced components | nominal UZS; +/-2pp sensitivity |
| Medium-term inflation target | 5.0% | AUTHORITATIVE_SOURCE | CBU monetary-policy concept | center of terminal-growth sensitivity, not a forecast |
| Terminal growth | 4% / 5% / 6% | CONFIGURABLE_RESEARCH_ASSUMPTION | CBU target-centered | bear/base/bull sensitivity |
| ROE | 28.8540% / 29.1995% / 29.5449% | SOURCE_DERIVED | audited IPKY 2023 + comparatives | bear/min, base/mean, bull/max |

The cost of equity is an explicit model estimate. The 16.96054% curve point is
never described or stored as WACC.

Source URLs:

- CBU monetary-policy concept: `https://cbu.uz/en/monetary-policy/concept/`
- Damodaran country-risk data: `https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/ctryprem.html`
- Damodaran global beta data: `https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/BetasGlobal.html`
- IPKY official audited report: `https://openinfo.uz/media/audit_conclusion/Аудиторское_заключение_МСФО_2023_DxdUBfo.pdf`
