#!/usr/bin/env python3
"""Build the T2W Fit Training App site (t2wfit.com) into docs/ (served by GitHub Pages).

Same system as team2ndwind.com (mr2ndwind/team2ndwind-site) and t2welite.com:
  content/pages/*.html   page bodies (key: value header, then ---, then HTML)
  content/faq.json       every FAQ answer, used by {{faq:Question|Question}}
  content/programs.json  one-time programs catalog (mirrors the GHL products), used by {{programs}}
  config.json            links (checkout), GHL form IDs, logo, contact info
Run:  python3 build.py

Tokens
  {{root}}                 relative path to site root
  {{img:path}}             image (GHL Media Storage map, absolute URLs pass through)
  {{link:key}}             checkout/purchase link from config.json > links (blank = falls back to Contact)
  {{form:inquiry}}         native GHL form
  {{faq:Q1|Q2}}            FAQ accordion + FAQPage schema (answers in content/faq.json)
  {{programs}}             one-time program cards grouped by category
  {{cta:Title|Text}}       closing CTA band
  {{quiz}}                 "Find my training option" quiz
  {{survey:key}}           native GHL survey embed (config surveys)
"""
import html, json, pathlib, re, shutil

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "docs"
CFG = json.loads((ROOT / "config.json").read_text())
SITE_URL = CFG["site_url"]
IMG_MAP = CFG.get("img_map", {})
FAQ = json.loads((ROOT / "content" / "faq.json").read_text())
PROGRAMS = json.loads((ROOT / "content" / "programs.json").read_text())


import hashlib as _h
CSS_V=_h.md5(open(__file__.replace("build.py","src/site.css"),"rb").read()).hexdigest()[:8]

def esc(s):
    return html.escape(s, quote=True)


def img_url(p):
    if p.startswith("http"):
        return p
    return IMG_MAP.get(p) or (CFG["img"] + p)


def parse_header(text):
    head, body = text.split("---\n", 1)
    meta = {}
    for line in head.strip().splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    return meta, body


def link(key):
    return CFG["links"].get(key) or "{{root}}contact/"


def form_embed(key):
    fid = CFG["forms"].get(key)
    h = CFG["form_heights"].get(key, 900)
    src = f'{CFG["form_host"]}/widget/form/{fid}'
    return (f'<div class="form-box" style="min-height:{h}px"><iframe src="{esc(src)}" id="inline-{fid}" '
            f'data-layout="{{\'id\':\'INLINE\'}}" data-trigger-type="alwaysShow" data-trigger-value="" '
            f'data-activation-type="alwaysActivated" data-activation-value="" data-deactivation-type="neverDeactivate" '
            f'data-deactivation-value="" data-form-name="{esc(key)}" data-height="{h}" data-layout-iframe-id="inline-{fid}" '
            f'data-form-id="{fid}" title="{esc(key)} form" '
            f'style="width:100%;height:100%;min-height:{h}px;border:none;border-radius:8px"></iframe></div>')


def survey_embed(key):
    sid = CFG["surveys"][key]
    h = CFG.get("survey_heights", {}).get(key, 700)
    src = f'{CFG["form_host"]}/widget/survey/{sid}'
    return (f'<div class="form-box" style="min-height:{h}px"><iframe src="{esc(src)}" id="{sid}" '
            f'style="border:none;width:100%;min-height:{h}px;border-radius:8px" scrolling="no" title="Plan finder survey"></iframe>'
            f'<script src="{CFG["form_host"]}/js/form_embed.js"></script></div>')


FAQ_USED = []


def faq_block(spec):
    out = []
    for q in [x.strip() for x in spec.split("|") if x.strip()]:
        if q not in FAQ:
            raise SystemExit(f"FAQ answer missing for: {q}")
        FAQ_USED.append((q, FAQ[q]))
        out.append(f"<details><summary>{esc(q)}</summary><p>{esc(FAQ[q])}</p></details>")
    return '<div class="faq">' + "".join(out) + "</div>"


def cta_band(spec):
    title, _, text = spec.partition("|")
    return (f'<section class="cta"><div class="wrap"><h2>{esc(title)}</h2><p>{esc(text)}</p>'
            f'<div class="btns" style="justify-content:center">'
            f'<a class="btn" href="{link("trial")}" rel="noopener">Start Your 14-Day Free Trial</a>'
            f'<a class="btn ghost" href="{{{{root}}}}plans/">Compare Plans</a></div></div></section>')


def programs_block():
    out = []
    for cat in PROGRAMS["categories"]:
        items = [p for p in PROGRAMS["programs"] if p["category"] == cat["key"]]
        if not items:
            continue
        cards = []
        for p in items:
            buy = p.get("buy_url") or "{{root}}contact/"
            label = "Get This Program" if p.get("buy_url") else "Ask a Coach"
            cards.append(
                f'<div class="card accent plan"><span class="eyebrow">{p["weeks"]}-Week Program</span><h3>{esc(p["name"])}</h3>'
                f'<p class="muted">{esc(p["blurb"])}</p><div class="price">${p["price"]}<small> one-time</small></div>'
                f'<p class="muted" style="margin-top:8px">{esc(p["best"])}</p>'
                f'<a class="btn sm" href="{buy}" rel="noopener">{label}</a></div>')
        out.append(f'<h3 id="{cat["key"]}" style="margin-top:48px">{esc(cat["title"])}</h3>'
                   f'<p class="muted">{esc(cat["intro"])}</p><div class="grid g3" style="margin-top:20px">{"".join(cards)}</div>')
    return "".join(out)


WORKOUTS = json.load(open(ROOT / "content" / "workouts.json"))


def workouts_block():
    types = ["Strength", "Cardio", "Mobility", "Recovery", "Core", "Flexibility", "Mindfulness", "Wellness"]
    chips = '<button type="button" class="on" data-f="all">All</button>' + "".join(
        f'<button type="button" data-f="{t.lower()}">{t}</button>' for t in types)
    cards = []
    for i, w in enumerate(WORKOUTS):
        tags = " ".join(x.strip().lower() for x in w["type"].split("/"))
        has_v = "1" if w["yt"] else "0"
        status = ('<span class="wk-play">&#9654; Watch Preview</span>' if w["yt"] else '<span class="wk-soon">Coming Soon</span>')
        cards.append(
            f'<article class="wk" data-i="{i}" data-tags="{esc(tags)}" data-v="{has_v}" data-s="{esc((w["name"] + " " + w["cat"] + " " + w["type"] + " " + w["desc"]).lower())}" tabindex="0" role="button" aria-haspopup="dialog">'
            f'<div class="wk-img"><img src="{esc(w["img"])}" alt="{esc(w["name"].title())} workout preview" loading="lazy"><span class="wk-tag">{esc(w["cat"])}</span></div>'
            f'<h3>{esc(w["name"])}</h3><p class="muted">{esc(w["desc"])}</p>'
            f'<div class="wk-foot"><span>{esc(w["dur"])}</span>{status}</div></article>')
    data = json.dumps([{k: w[k] for k in ("cat", "name", "desc", "dur", "level", "type", "benefits", "equip", "yt")} for w in WORKOUTS], ensure_ascii=False).replace("</", "<\\/")
    dlg = ('<dialog id="wk-dlg" class="wk-dlg"><button type="button" class="wk-x" aria-label="Close">&times;</button>'
           '<div class="wk-media" id="wk-media"></div><div class="wk-body"><span class="eyebrow" id="wk-cat"></span><h3 id="wk-name"></h3>'
           '<dl class="wk-meta"><div><dt>Duration</dt><dd id="wk-dur"></dd></div><div><dt>Level</dt><dd id="wk-lvl"></dd></div><div><dt>Training type</dt><dd id="wk-type"></dd></div></dl>'
           '<h4>Focus &amp; Benefits</h4><ul class="checks" id="wk-ben"></ul>'
           '<p class="wk-eq"><b>Equipment:</b> <span id="wk-eq"></span></p>'
           '<div class="btns"><a class="btn" href="' + link("trial") + '" rel="noopener">Unlock Full Access</a><a class="btn ghost" href="{{root}}contact/">Ask My Coach</a></div>'
           '<p class="muted" style="font-size:.8rem;margin-top:14px">Public preview shown. Additional guided workouts and personalized programming are available through qualifying T2W Fit memberships.</p></div></dialog>')
    js = "<script>" + open(ROOT / "src" / "workouts.js").read().replace("__DATA__", data) + "</script>"
    return ('<div class="wk-tools"><div class="filters" id="wk-filters">' + chips + '</div>'
            '<div class="wk-row"><label class="wk-toggle"><input type="checkbox" id="wk-video"> <span>Video available</span></label>'
            '<input type="search" id="wk-search" placeholder="Search workouts..." aria-label="Search workouts"></div></div>'
            f'<div class="wk-grid" id="wk-grid">{"".join(cards)}</div><p class="muted" id="wk-empty" hidden style="margin-top:20px">No workouts match. Try another filter or search.</p>'
            + dlg + js)


QUIZ = """<div class="quiz" id="quiz"><span class="eyebrow">2-Minute Plan Finder</span><h3 id="q-title">What do you want most from your training?</h3>
<div class="opts" id="q-opts"></div>
<div class="result" id="q-res"></div></div>
<script>
(function(){var root='{{root}}';
var steps=[
{t:'What do you want most from your training?',o:[['I want workouts I can do on my own schedule','od'],['I want a plan and some accountability','dp'],['I want a coach to personalize everything','oc'],['I want in-person coaching plus the app','hy']]},
{t:'How much support do you want?',o:[['Just the workouts','od'],['A structured plan and check-ins','dp'],['A real coach in my corner','oc'],['A coach in the studio and in the app','hy']]}];
var rec={od:['T2W Fit On-Demand','$14.99/mo','Train anytime with the full workout library. Includes a 14-day free trial.',root+'plans/#on-demand'],
dp:['T2W Fit Digital Plus','$34.99/mo','Scheduled plans, goal-based recommendations, habit tracking and monthly goal reviews.',root+'plans/#digital-plus'],
oc:['T2W Online Coaching','Starting at $79/mo','Personalized programming, weekly check-ins and direct coach messaging.',root+'plans/#online-coaching'],
hy:['T2W Hybrid Coaching','See plans','Weekly one-on-one training at the studio plus personalized app coaching.',root+'plans/#hybrid-coaching']};
var tally={od:0,dp:0,oc:0,hy:0},i=0,t=document.getElementById('q-title'),o=document.getElementById('q-opts'),r=document.getElementById('q-res');
function show(){var s=steps[i];t.textContent=s.t;o.innerHTML='';s.o.forEach(function(x){var b=document.createElement('button');b.textContent=x[0];b.onclick=function(){tally[x[1]]++;i++;if(i<steps.length){show()}else{done()}};o.appendChild(b)})}
function done(){var k=Object.keys(tally).sort(function(a,b){return tally[b]-tally[a]})[0],p=rec[k];t.textContent='Your best starting point';o.innerHTML='';
r.className='result show';r.innerHTML='<h3>'+p[0]+'</h3><p class="muted">'+p[2]+'</p><div class="price">'+p[1]+'</div><div class="btns"><a class="btn" href="'+p[3]+'">See This Plan</a><a class="btn ghost" href="'+root+'contact/">Ask a Coach</a></div>'}
show()})();
</script>"""


def render_tokens(body):
    FAQ_USED.clear()
    body = re.sub(r"\{\{faq:(.+?)\}\}", lambda m: faq_block(m.group(1)), body)
    body = re.sub(r"\{\{link:([a-z_0-9]+)\}\}", lambda m: link(m.group(1)), body)
    body = re.sub(r"\{\{form:([a-z_]+)\}\}", lambda m: form_embed(m.group(1)), body)
    body = re.sub(r"\{\{survey:([a-z_]+)\}\}", lambda m: survey_embed(m.group(1)), body)
    body = re.sub(r"\{\{cta:(.+?)\}\}", lambda m: cta_band(m.group(1)), body)
    body = re.sub(r"\{\{img:(.+?)\}\}", lambda m: img_url(m.group(1)), body)
    body = body.replace("{{programs}}", programs_block()).replace("{{quiz}}", QUIZ).replace("{{workouts}}", workouts_block())
    body = body.replace("{{phone}}", CFG["phone_display"]).replace("{{tel}}", CFG["phone_tel"]).replace("{{email}}", CFG["email"])
    schema = None
    if FAQ_USED:
        schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ_USED]}
    return body, schema


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def layout(title, desc, path, body, active=None, schema=None, noindex=False):
    root = "../" * path.count("/")
    canon = f"{SITE_URL}/{path}"
    on = ' class="on"'

    def nl(n, p):
        return f'<a href="{root}{p}"{on if active == p else ""}>{n}</a>'

    nav = (nl("Plans", "plans/") + nl("Programs", "programs/") + nl("Transformations", "transformation-programs/")
           + nl("Features", "features/") + nl("Workout Library", "workout-library/") + nl("Challenges", "challenges/")
           + nl("Success Stories", "success-stories/") + nl("FAQ", "faq/")
           + f'<a href="{CFG["login_url"]}" rel="noopener">Log In</a>'
           + f'<a class="btn sm" href="{link("trial").replace("{{root}}", root)}" rel="noopener">14 Days Free</a>')
    schemas = schema if isinstance(schema, list) else ([schema] if schema else [])
    ld = "".join(f'<script type="application/ld+json">{json.dumps(s)}</script>' for s in schemas)
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ""
    page = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">{robots}
<meta property="og:type" content="website"><meta property="og:site_name" content="T2W Fit Training App">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}"><meta property="og:image" content="{CFG['og_image']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0A0A0B">
<link rel="icon" href="{CFG['logo']}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/site.css?v={CSS_V}">
{ld}
</head><body>
<header class="top"><div class="wrap">
<a class="logo" href="{root or './'}" aria-label="T2W Fit Training App home"><img src="{CFG.get('nav_logo',CFG['logo'])}" alt="T2W Fit Digital" width="140" height="52"></a>
<button class="menu-btn" aria-expanded="false" aria-controls="nav">MENU</button>
<nav class="nav" id="nav">{nav}</nav>
</div></header>
<main>
{body}
</main>
<footer><div class="wrap">
<div class="foot">
<div><img src="{CFG.get('nav_logo',CFG['logo'])}" alt="T2W Fit Digital" width="150" height="56" style="height:56px;width:auto;margin-bottom:16px">
<p class="muted">Coach-led fitness, athletic performance, accountability, and workouts built for real life.</p>
<p class="tag">MAKE MOVES, NOT EXCUSES.</p>
<a class="btn sm" href="{link("trial").replace("{{root}}", root)}" rel="noopener">Start 14 Days Free</a></div>
<div><h4>Explore</h4><ul>
<li><a href="{root}plans/">Plans &amp; Pricing</a></li>
<li><a href="{root}programs/">One-Time Programs</a></li>
<li><a href="{root}transformation-programs/">Transformation Programs</a></li>
<li><a href="{root}features/">App Features</a></li>
<li><a href="{root}workout-library/">Workout Library</a></li>
<li><a href="{root}challenges/">Challenges Hub</a></li>
<li><a href="{root}success-stories/">Success Stories</a></li>
<li><a href="{root}coach/">Meet Coach Corey</a></li>
<li><a href="{root}faq/">FAQ</a></li></ul></div>
<div><h4>Legal &amp; Policies</h4><ul>
<li><a href="{root}terms-of-service/">Terms of Service</a></li>
<li><a href="{root}privacy-policy/">Privacy Policy</a></li>
<li><a href="{root}refund-policy/">Refund &amp; Cancellation</a></li>
<li><a href="{root}medical-disclaimer/">Medical Disclaimer</a></li>
<li><a href="{root}waiver/">Liability Waiver</a></li></ul></div>
<div><h4>Connect</h4><ul>
<li><a href="{CFG['login_url']}" rel="noopener">Member Log In</a></li>
<li><a href="{root}contact/">Contact Us</a></li>
<li><a href="tel:{CFG['phone_tel']}">{CFG['phone_display']}</a></li>
<li><a href="mailto:{CFG['email']}">{CFG['email']}</a></li>
<li><a href="{CFG['facebook']}" rel="noopener">Facebook</a> &middot; <a href="{CFG['instagram']}" rel="noopener">Instagram</a></li>
<li><a href="{CFG['studio_url']}" rel="noopener">Train in the Studio (Broken Arrow, OK)</a></li></ul></div>
</div>
<div class="legal"><span>&copy; <span id="yr">2026</span> Team 2nd Wind LLC | T2W Fit. All rights reserved.</span>
<span>T2W Fit Training App is powered by Trainerize.</span></div>
</div></footer>
<script>
document.getElementById('yr').textContent=new Date().getFullYear();
var b=document.querySelector('.menu-btn'),n=document.getElementById('nav');
b.addEventListener('click',function(){{var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)}});
</script>
<script src="{CFG['form_host']}/js/form_embed.js"></script>
</body></html>
"""
    page = page.replace("{{root}}", root)
    dest = OUT / path / "index.html" if path else OUT / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page)
    write_ghl_snippet(page, path)
    return None if noindex else canon


def write_ghl_snippet(page, path):
    """Self-contained snippet for a GHL Custom Code element (docs/_ghl/<slug>.html), same as the studio site."""
    css = (ROOT / "src" / "site.css").read_text()
    body = re.search(r"<body>(.*)</body>", page, re.S).group(1)
    fonts = re.search(r'<link href="https://fonts.googleapis.com[^>]+>', page).group(0)

    def fix(m):
        attr, val = m.group(1), m.group(2)
        if re.match(r"(https?:|tel:|mailto:|#|//|data:)", val):
            return m.group(0)
        v = val
        while v.startswith("../"):
            v = v[3:]
        if v in ("./", ""):
            v = ""
        return f'{attr}="{SITE_URL}/{v}"'

    body = re.sub(r'(href|src)="([^"]*)"', fix, body)
    snippet = f'{fonts}\n<style>\n{css}\nhtml,body{{background:#0A0A0B!important;overflow-x:hidden}}\n</style>\n<div class="t2w-ghl" style="background:#0A0A0B">\n{body}\n</div>\n'
    d = OUT / "_ghl"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{slugify(path) if path else 'home'}.html").write_text(snippet)


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    shutil.copy(ROOT / "src" / "site.css", OUT / "assets" / "site.css")
    urls = []
    for f in sorted((ROOT / "content" / "pages").glob("*.html")):
        meta, body = parse_header(f.read_text())
        body, faq_schema = render_tokens(body)
        schema = [faq_schema] if faq_schema else []
        if meta["path"] == "":
            schema.append({"@context": "https://schema.org", "@type": "Organization", "name": "T2W Fit Training App",
                           "alternateName": "Team 2nd Wind", "url": SITE_URL, "logo": CFG["logo"], "email": CFG["email"],
                           "telephone": "+1-918-918-3234", "sameAs": [CFG["facebook"], CFG["instagram"]]})
        urls.append(layout(meta["title"], meta["description"], meta["path"], body,
                           active=meta.get("nav", meta["path"]), schema=schema, noindex=meta.get("noindex") == "yes"))
    (OUT / "404.html").write_text((OUT / "not-found" / "index.html").read_text().replace('href="../', 'href="/').replace('src="../', 'src="/'))
    shutil.rmtree(OUT / "not-found")
    urls = sorted({u for u in urls if u and "not-found" not in u})
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    (OUT / ".nojekyll").write_text("")
    if CFG.get("custom_domain"):
        (OUT / "CNAME").write_text(CFG["custom_domain"] + "\n")
    print(f"Built {len(urls)} indexable pages into {OUT}")


if __name__ == "__main__":
    build()
