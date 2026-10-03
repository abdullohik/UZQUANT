# Clean-Checkout Prototype Verification

Date: 2026-10-03

The local candidate commit was checked out into an isolated temporary clone and verified without using development-tree source files.

## Results

- Full clean-checkout test suite: **234 passed**
- Focused adversarial suite: **48 passed**
- Python source compilation: **passed**
- JavaScript syntax validation: **passed**
- Local server startup: **passed**
- `/api/v1/health` smoke request: **200 OK**
- `/api/v1/coverage` production-data smoke request: **200 OK, 73 securities**
- Development and clean-checkout suite counts agree: **yes**

The two production-database tests skip in a source-only archive because runtime evidence databases are intentionally not committed. The final clean-checkout run linked the same production evidence database read-only in the clean checkout, matching the prior verification method. Source code came exclusively from the exact committed SHA. No database record was manually edited. The temporary checkout was used only for verification.
