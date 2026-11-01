#!/usr/bin/env python3
"""Generate per-post and per-meme link-preview pages and Open Graph images.

For every blog post and meme, this writes:
  images/og/<slug>.jpg          1200x630 preview image (< 280 KB for WhatsApp/X/LinkedIn)
  p/<slug>.html                 static page with og:/twitter: tags that redirects humans to blog.html?post=<slug>
  p/<slug>/index.html           directory index fallback so trailing-slash /p/<slug>/ never 404s
  images/og/memes/<id>.jpg      1200x630 meme preview image
  m/<id>.html                   static meme page that redirects humans to memes.html?meme=<id>
  m/<id>/index.html             directory index fallback so trailing-slash /m/<id>/ never 404s

Run from anywhere:     python3 tools/generate_previews.py
"""
import json, os, html, re
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://syedshubha.com'
W, H = 1200, 630
BG = (22, 11, 40)  # site navy
PAD = 36

def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s or '')

def make_og_image(cover_path, out_path):
    im = Image.open(cover_path)
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        flat = Image.new('RGB', im.size, (255, 255, 255))
        flat.paste(im, mask=im.split()[3])
        im = flat
    else:
        im = im.convert('RGB')
    scale = min((W - 2 * PAD) / im.width, (H - 2 * PAD) / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    canvas = Image.new('RGB', (W, H), BG)
    canvas.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
    for q in (90, 85, 80, 75, 70):
        canvas.save(out_path, 'JPEG', quality=q, optimize=True, subsampling=0)
        if os.path.getsize(out_path) < 280_000:
            break
    return os.path.getsize(out_path)

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Syed Emad Uddin Shubha</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">

<meta property="og:type" content="article">
<meta property="og:site_name" content="Syed Emad Uddin Shubha">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{img}">
<meta property="og:image:secure_url" content="{img}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="{w}">
<meta property="og:image:height" content="{h}">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{img}">
<meta name="twitter:creator" content="@syed_shubha">

<meta http-equiv="refresh" content="0; url={target}">
<script>window.location.replace("{target}");</script>
</head>
<body style="font-family:Georgia,serif;background:#160b28;color:#f4effa;padding:2rem">
<h1>{title}</h1>
<p>{desc}</p>
<p><a style="color:#d4af37" href="{target}">Continue to page &rarr;</a></p>
</body>
</html>
"""

def main():
    data = json.load(open(os.path.join(ROOT, 'data', 'portfolio_data.json')))
    os.makedirs(os.path.join(ROOT, 'images', 'og'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'images', 'og', 'memes'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'p'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'm'), exist_ok=True)
    fallback_cover = os.path.join(ROOT, 'images', 'peano_and_dedekind_gap.png')
    made = []
    for p in data['posts']:
        if p.get('hide_from_blog'):
            continue
        slug = p.get('slug') or p['id']
        cover_rel = p.get('cover_image')
        cover_abs = os.path.join(ROOT, cover_rel) if cover_rel else fallback_cover
        size = make_og_image(cover_abs, os.path.join(ROOT, 'images', 'og', f'{slug}.jpg'))
        page = PAGE.format(
            title=html.escape(strip_tags(p['title']), quote=True),
            desc=html.escape(strip_tags(p.get('summary', '')), quote=True),
            url=f'{SITE}/p/{slug}',
            img=f'{SITE}/images/og/{slug}.jpg',
            w=W, h=H,
            target=f'/blog.html?post={slug}',
        )
        open(os.path.join(ROOT, 'p', f'{slug}.html'), 'w').write(page)
        slug_dir = os.path.join(ROOT, 'p', slug)
        os.makedirs(slug_dir, exist_ok=True)
        open(os.path.join(slug_dir, 'index.html'), 'w').write(page)
        made.append((f'/p/{slug}', size))

    meme_made = []
    for m in data.get('memes', []):
        if not m.get('image'):
            continue
        mid = m['id']
        size = make_og_image(os.path.join(ROOT, m['image']), os.path.join(ROOT, 'images', 'og', 'memes', f'{mid}.jpg'))
        desc_raw = strip_tags(m.get('desc') or m.get('description') or m.get('explanation') or '')
        page = PAGE.format(
            title=html.escape(f"{strip_tags(m['title'])} | Quantum Memeology", quote=True),
            desc=html.escape(desc_raw, quote=True),
            url=f'{SITE}/m/{mid}',
            img=f'{SITE}/images/og/memes/{mid}.jpg',
            w=W, h=H,
            target=f'/memes.html?meme={mid}',
        )
        open(os.path.join(ROOT, 'm', f'{mid}.html'), 'w').write(page)
        mid_dir = os.path.join(ROOT, 'm', mid)
        os.makedirs(mid_dir, exist_ok=True)
        open(os.path.join(mid_dir, 'index.html'), 'w').write(page)
        meme_made.append((f'/m/{mid}', size))

    for path, size in made:
        print(f'{SITE}{path}   (og image {size // 1024} KB)')
    print(f'Generated {len(meme_made)} meme preview pages under {SITE}/m/<id> (max og image {max(s for _, s in meme_made) // 1024} KB)')

if __name__ == '__main__':
    main()
