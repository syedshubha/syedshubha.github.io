#!/usr/bin/env python3
"""Generate per-post link-preview pages and Open Graph images.

For every blog post that has a cover image, this writes:
  images/og/<slug>.jpg   1200x630 preview image (cover centered on navy, < 300 KB for WhatsApp)
  p/<slug>.html          static page with og:/twitter: tags that redirects humans to blog.html?post=<slug>

Share URL for a post:  https://syedshubha.com/p/<slug>
Run from anywhere:     python3 tools/generate_previews.py
"""
import json, os, html
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://syedshubha.com'
W, H = 1200, 630
BG = (22, 11, 40)  # site navy
PAD = 36

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
<p><a style="color:#d4af37" href="{target}">Read the article &rarr;</a></p>
</body>
</html>
"""

def main():
    data = json.load(open(os.path.join(ROOT, 'data', 'portfolio_data.json')))
    os.makedirs(os.path.join(ROOT, 'images', 'og'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'p'), exist_ok=True)
    made = []
    for p in data['posts']:
        if p.get('hide_from_blog') or not p.get('cover_image'):
            continue
        slug = p.get('slug') or p['id']
        size = make_og_image(os.path.join(ROOT, p['cover_image']), os.path.join(ROOT, 'images', 'og', f'{slug}.jpg'))
        page = PAGE.format(
            title=html.escape(p['title'], quote=True),
            desc=html.escape(p.get('summary', ''), quote=True),
            url=f'{SITE}/p/{slug}',
            img=f'{SITE}/images/og/{slug}.jpg',
            w=W, h=H,
            target=f'/blog.html?post={slug}',
        )
        open(os.path.join(ROOT, 'p', f'{slug}.html'), 'w').write(page)
        made.append((slug, size))
    for slug, size in made:
        print(f'{SITE}/p/{slug}   (og image {size // 1024} KB)')

if __name__ == '__main__':
    main()
