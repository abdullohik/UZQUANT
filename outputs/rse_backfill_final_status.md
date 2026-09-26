# RSE backfill final status

- Original pending queue: 1,885
- Processed this sprint: 81 (50 imported; 31 verified empty)
- Final queue: 61 `IMPORTED`, 34 `EMPTY` (`VERIFIED_EMPTY` in reporting), 1,804 `PENDING` (`RETRY_PENDING`), 1 `SOURCE_BLOCKED`, 0 `IN_PROGRESS`, 0 parser failures.
- Archived pages: 268 (143 new)
- Exact trade rows: 9,870 (3,997 new)
- Market observations: 551
- Unique dates: 73
- Span: 2024-09-27–2026-09-25
- Stop reason: public RSE returned HTTP 429 after the bounded run; collector interruption returned the active job to `PENDING`.
- Resume command remains deterministic and idempotent: `backfill-rse-html --job-limit N --pause-seconds S`.
- No price was forward-filled and no empty window became a synthetic zero-return observation.
