# ArmTune Serve — Website (Next.js)

Black-theme product and documentation site for ArmTune Serve, deployable to
Vercel.

## Run locally

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Build

```bash
npm run build
```

The static export is written to `out/`.

> **Windows note:** this repository currently lives on an exFAT drive, and
> Node's `fs.readlink` fails on exFAT, which breaks local Next.js builds
> (`EISDIR: illegal operation on a directory, readlink`). Build on an NTFS
> drive (verified working) or use the Vercel build pipeline, which runs on
> Linux and is unaffected.

## Deploy to Vercel

1. Push this repository to GitHub.
2. In Vercel, **Add New Project** and import `luxmikant/Arm-Tune`.
3. Set **Root Directory** to `web`.
4. Framework preset: **Next.js**. Build command and output directory are
   detected automatically (`next build` with static export).
5. Deploy.

The site uses `output: 'export'` so it deploys as a pure static site with no
server runtime.
