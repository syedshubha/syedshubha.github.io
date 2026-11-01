#!/usr/bin/env python3
"""Generate per-post and per-meme pages, clean directory routes (/blog/, /memes/, /qsvt/), and Open Graph images.

For every blog post and meme, this writes:
  images/og/<slug>.jpg          1200x630 preview image (< 280 KB for WhatsApp/X/LinkedIn)
  p/<slug>.html                 full zero-redirect blog reader page with custom og:/twitter: tags
  p/<slug>/index.html           directory index so /p/<slug> and /p/<slug>/ render in-place with zero redirect
  images/og/memes/<id>.jpg      1200x630 meme preview image
  m/<id>.html                   full zero-redirect meme page with custom og:/twitter: tags
  m/<id>/index.html             directory index so /m/<id> and /m/<id>/ render in-place with zero redirect
  blog/index.html               clean /blog/ route
  memes/index.html              clean /memes/ route
  qsvt/index.html               clean /qsvt/ route

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

META_BLOCK = """    <base href="/">
    <title>{title} | Syed Emad Uddin Shubha</title>
    <meta name="description" content="{desc}">
    <link rel="canonical" href="{url}">

    <!-- Open Graph / LinkedIn / Facebook -->
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

    <!-- Twitter / X -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="{url}">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{desc}">
    <meta name="twitter:image" content="{img}">
    <meta name="twitter:creator" content="@syed_shubha">
    <script>{init_js}</script>"""

def inject_meta(template_html, meta_block):
    pattern = re.compile(r'<title>.*?</title>.*?<meta name="twitter:creator"[^>]*>', re.DOTALL)
    return pattern.sub(lambda _: meta_block, template_html, count=1)

def main():
    data = json.load(open(os.path.join(ROOT, 'data', 'portfolio_data.json'), encoding='utf-8'))
    blog_tpl = open(os.path.join(ROOT, 'blog.html'), encoding='utf-8').read()
    memes_tpl = open(os.path.join(ROOT, 'memes.html'), encoding='utf-8').read()

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
        cover_rel = (p.get('cover_image') or '').lstrip('/')
        cover_abs = os.path.join(ROOT, cover_rel) if cover_rel else fallback_cover
        size = make_og_image(cover_abs, os.path.join(ROOT, 'images', 'og', f'{slug}.jpg'))
        meta = META_BLOCK.format(
            title=html.escape(strip_tags(p['title']), quote=True),
            desc=html.escape(strip_tags(p.get('summary', '')), quote=True),
            url=f'{SITE}/p/{slug}',
            img=f'{SITE}/images/og/{slug}.jpg',
            w=W, h=H,
            init_js=f'window.__INITIAL_POST_SLUG__ = {json.dumps(slug)};',
        )
        page = inject_meta(blog_tpl, meta)
        open(os.path.join(ROOT, 'p', f'{slug}.html'), 'w', encoding='utf-8').write(page)
        slug_dir = os.path.join(ROOT, 'p', slug)
        os.makedirs(slug_dir, exist_ok=True)
        open(os.path.join(slug_dir, 'index.html'), 'w', encoding='utf-8').write(page)
        made.append((f'/p/{slug}', size))

    meme_made = []
    for m in data.get('memes', []):
        if not m.get('image'):
            continue
        mid = m['id']
        size = make_og_image(os.path.join(ROOT, m['image'].lstrip('/')), os.path.join(ROOT, 'images', 'og', 'memes', f'{mid}.jpg'))
        desc_raw = strip_tags(m.get('desc') or m.get('description') or m.get('explanation') or '')
        meta = META_BLOCK.format(
            title=html.escape(f"{strip_tags(m['title'])} | Quantum Memeology", quote=True),
            desc=html.escape(desc_raw, quote=True),
            url=f'{SITE}/m/{mid}',
            img=f'{SITE}/images/og/memes/{mid}.jpg',
            w=W, h=H,
            init_js=f'window.__INITIAL_MEME_ID__ = {json.dumps(mid)};',
        )
        page = inject_meta(memes_tpl, meta)
        open(os.path.join(ROOT, 'm', f'{mid}.html'), 'w', encoding='utf-8').write(page)
        mid_dir = os.path.join(ROOT, 'm', mid)
        os.makedirs(mid_dir, exist_ok=True)
        open(os.path.join(mid_dir, 'index.html'), 'w', encoding='utf-8').write(page)
        meme_made.append((f'/m/{mid}', size))

    # Generate clean directory index pages: /blog/, /memes/, /qsvt/
    for src_file, dest_dir in [('blog.html', 'blog'), ('memes.html', 'memes'), ('QSVT.html', 'qsvt')]:
        src_path = os.path.join(ROOT, src_file)
        if not os.path.exists(src_path):
            continue
        raw_html = open(src_path, 'r', encoding='utf-8').read()
        if '<base ' not in raw_html:
            raw_html = raw_html.replace('<head>', '<head>\n    <base href="/">', 1)
        out_dir = os.path.join(ROOT, dest_dir)
        os.makedirs(out_dir, exist_ok=True)
        open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8').write(raw_html)

    for path, size in made:
        print(f'{SITE}{path}   (og image {size // 1024} KB)')
    print(f'Generated {len(meme_made)} meme preview pages under {SITE}/m/<id> (max og image {max(s for _, s in meme_made) // 1024} KB)')

if __name__ == '__main__':
    main()
