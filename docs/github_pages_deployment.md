# GitHub Pages Deployment

UZQUANT's GitHub Pages build is a read-only, backend-derived research snapshot. GitHub Pages never runs Python and never receives the SQLite database, raw source documents, credentials, or writable analytical state.

## Publish a refreshed snapshot

From a verified local production environment:

```bash
python -m pytest -q
python -m uzquant.static_site export \
  --database data/uzquant.sqlite3 \
  --output site \
  --source-revision "$(git rev-parse HEAD)"
python -m uzquant.static_site verify --output site
```

Review the generated `site/data/manifest.json` and the Git diff before committing. A push to `main` that changes `site/` triggers `.github/workflows/pages.yml`, which tests the committed source, validates the snapshot, and deploys the static artifact.

## Accuracy and security boundary

- Python remains the analytical source of truth.
- The browser performs presentation and filtering only.
- Missing fields remain missing in the exported API payloads.
- The export is immutable until a later validated snapshot is committed.
- Source URLs and evidence lineage intentionally remain visible.
- The SQLite database, raw source documents, local paths, credentials, and secrets are not published.
- GitHub Actions does not regenerate production research without an approved persistent evidence source. It deploys the already validated snapshot and therefore cannot silently replace unavailable evidence.

## GitHub configuration

In repository **Settings → Pages**, select **GitHub Actions** as the build and deployment source. The public URL will normally be:

`https://abdullohik.github.io/UZQUANT/`

Publishing is a separate external action. Preparing or validating the static snapshot does not itself make any data public.
