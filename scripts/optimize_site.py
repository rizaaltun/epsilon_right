"""Download original covers, create verified WebP variants, and update references.
Run from repository root with Pillow installed. Failed downloads retain originals.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
import hashlib, html, io, json, re, time
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'assets/cover-manifest.json'
PATTERN = re.compile(r'https://www\.epsilonyayingrubu\.com/Icerik/Gorsel/Urun/[^\s"<>]+')

def main():
    files = list(ROOT.rglob('*.html')) + [ROOT / 'assets/meta.json']
    urls = sorted({html.unescape(u) for p in files for u in PATTERN.findall(p.read_text())})
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    urls = sorted(set(urls) | set(manifest))
    out = ROOT / 'assets/images/covers'
    out.mkdir(parents=True, exist_ok=True)
    def convert(url):
        old = manifest.get(url)
        if old and all((ROOT / v['path']).exists() for v in old['variants']): return url, old
        data = None
        for attempt in range(3):
            try:
                with urlopen(Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=60) as r:
                    data = r.read()
                with Image.open(io.BytesIO(data)) as check: check.verify()
                break
            except Exception:
                if attempt == 2: raise
                time.sleep(attempt + 1)
        with Image.open(io.BytesIO(data)) as original:
            image = ImageOps.exif_transpose(original).convert('RGB')
            width, height = image.size
            variants = []
            stem = hashlib.sha256(url.encode()).hexdigest()[:20]
            for target in sorted(set([min(480,width),min(1000,width)])):
                resized = image.copy()
                resized.thumbnail((target, round(height * target / width)),Image.Resampling.LANCZOS)
                dest = out / f'{stem}-{target}.webp'
                resized.save(dest,'WEBP',quality=86,method=6)
                with Image.open(dest) as verify:
                    verify.load()
                    assert verify.size == resized.size
                variants.append({'path':dest.relative_to(ROOT).as_posix(),'width':resized.width,'height':resized.height,'bytes':dest.stat().st_size})
        return url, {'original_bytes':len(data),'original_width':width,'original_height':height,'variants':variants}
    failures = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        tasks = {pool.submit(convert,u):u for u in urls}
        for i, future in enumerate(as_completed(tasks),1):
            try:
                url, record = future.result(); manifest[url] = record
            except Exception as e:
                failures.append({'url':tasks[future],'error':str(e)})
            if i % 20 == 0: print(f'{i}/{len(urls)} covers processed',flush=True)
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    for p in files:
        source = p.read_text(); prefix = '../' * len(p.relative_to(ROOT).parts[:-1])
        if p.suffix == '.json':
            meta = json.loads(source)
            for item in meta.values():
                if item.get('p') in manifest: item['p'] = '/' + manifest[item['p']]['variants'][-1]['path']
            result = json.dumps(meta,ensure_ascii=False,separators=(',',':'))+'\n'
        else:
            image_count = [0]
            def replace_img(match):
                tag = match.group(0)
                src = re.search(r'\bsrc="([^"]+)"',tag)
                if not src or html.unescape(src[1]) not in manifest: return tag
                record = manifest[html.unescape(src[1])]; variants = record['variants']
                tag = tag.replace(src[0],f'src="{prefix}{variants[-1]["path"]}"')
                tag = re.sub(r'\s(?:srcset|sizes|loading|fetchpriority)="[^"]*"','',tag)
                detail = len(p.relative_to(ROOT).parts) == 3 and p.relative_to(ROOT).parts[0] == 'books'
                priority = detail and image_count[0] == 0
                image_count[0] += 1
                attrs = ' srcset="' + ', '.join(f'{prefix}{v["path"]} {v["width"]}w' for v in variants) + '"'
                attrs += ' sizes="(min-width: 1024px) 420px, 90vw"' if priority else ' sizes="(min-width: 1280px) 220px, (min-width: 640px) 30vw, 45vw"'
                attrs += ' loading="eager" fetchpriority="high"' if priority else ' loading="lazy"'
                return tag[:-2]+attrs+'/>' if tag.endswith('/>') else tag[:-1]+attrs+'>'
            result = re.sub(r'<img\b[^>]*>',replace_img,source)
            result = re.sub(r'<footer\b.*?</footer>', lambda m: re.sub(r'<li><a\b[^>]*href="[^"]*/?services/"[^>]*>Services</a></li>', '', m[0]), result, flags=re.S)
        if result != source: p.write_text(result)
    report = {'covers':len(manifest),'original_bytes':sum(v['original_bytes'] for v in manifest.values()),'large_webp_bytes':sum(v['variants'][-1]['bytes'] for v in manifest.values()),'small_webp_bytes':sum(v['variants'][0]['bytes'] for v in manifest.values()),'failures':failures}
    (ROOT/'assets/cover-optimization-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
    if failures: raise SystemExit('Some originals could not be downloaded; original references were preserved.')

if __name__ == '__main__': main()
