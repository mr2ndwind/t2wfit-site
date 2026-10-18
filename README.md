# t2wfit.com (T2W Fit Training App)

Static site built the same way as team2ndwind.com and t2welite.com. Replaces the GHL Vibe Studio build of t2wfit.com.

- `content/pages/*.html` page bodies (header block, then `---`, then HTML)
- `content/faq.json` FAQ answers used by `{{faq:Question|Question}}`
- `content/programs.json` one-time programs (mirrors the 27 GHL program products; set `buy_url` per program when GHL checkout links exist)
- `config.json` logo, checkout links (`links`), GHL form IDs, contact info. A blank link falls back to /contact/
- `src/site.css` shared T2W Fit Studio styling (amber #FEA82F on black)
- `build.py` run `python3 build.py` to regenerate `docs/` (GitHub Pages serves /docs). `docs/_ghl/<slug>.html` are code-block snippets for GHL.

URL parity with the old Vibe site: /transformation-programs, /features, /workout-library, /challenges, /success-stories, /terms-of-service, /privacy-policy, /refund-policy, /medical-disclaimer, /waiver.
