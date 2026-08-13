# ArmTune Serve product website

The static product and documentation site lives in `site/`.

## Local preview

From the repository root:

```bash
python -m http.server 4173 --directory site
```

Open `http://127.0.0.1:4173/`.

## GitHub Pages

The `deploy-pages.yml` workflow publishes `site/` whenever changes land on
`main` under `site/`.

The first deployment requires one repository setting because the workflow
token cannot enable Pages on its own (GitHub's configure-pages action only
allows programmatic enablement with a personal access token):

1. Open GitHub repository **Settings > Pages**.
2. Set **Source** to **GitHub Actions**.
3. Run **Actions > Deploy product website > Run workflow**.

After step 2, every push to `site/` deploys automatically.

Expected URL:

```text
https://luxmikant.github.io/Arm-Tune/
```

The site intentionally has no npm, bundler, or JavaScript framework. It is a
small, auditable static site that can be hosted by GitHub Pages, a CDN, or any
ordinary web server.
