import json, urllib.request, urllib.parse

recs = json.load(open(r'D:\Projects\ViDrive Web\SEO\heytony.agency.reels_index.json', encoding='utf-8'))
u = [r for r in recs if r['shortcode'] == 'C1DJiA1ODrY'][0]['og_video']
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
tests = [
    ('no-range', {}),
    ('range0-1000', {'Range': 'bytes=0-1000'}),
    ('range0-1240797', {'Range': 'bytes=0-1240797'}),
    ('range0-1240797+ref', {'Range': 'bytes=0-1240797', 'Referer': 'https://www.instagram.com/'}),
    ('range0-5000000', {'Range': 'bytes=0-5000000'}),
    ('range1240798-3174593', {'Range': 'bytes=1240798-3174593'}),
]
for name, hdr in tests:
    try:
        req = urllib.request.Request(u, headers={**UA, **hdr})
        with urllib.request.urlopen(req, timeout=60) as r:
            b = r.read()
        cr = r.headers.get('Content-Range', '')
        has_moov = b'moov' in b[:200000]
        print(f'{name:22} {r.status} len={len(b):8} CR={cr} moov={has_moov}')
    except Exception as e:
        print(f'{name:22} ERR {e}')