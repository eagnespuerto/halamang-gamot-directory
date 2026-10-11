"""Split the Project Gutenberg edition of The Medicinal Plants of the Philippines
(ebook 26393) into one record per plant and write data/book.json.

    python scripts/parse_book.py

The source HTML is downloaded to data/source/ on first run.
"""
import re, json, html, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'data' / 'source' / 'pg26393.html'
OUT = ROOT / 'data' / 'book.json'
if not SRC.exists():
    SRC.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve('https://www.gutenberg.org/cache/epub/26393/pg26393-images.html', SRC)
src = SRC.read_text(encoding='utf-8')
a = src.index('<h2 class="super">Medicinal Plants of the Philippines</h2>')
body = src[a:]
body = body.replace('<p><span class="smallcaps">Coriandrum sativum</span>,', '<p><b>Coriandrum sativum</b>,')
body = re.sub(r'Blanco\.\)<br>\s*2\. <b>G\. Cambogia</b>', 'Blanco.)</p><p>2. <b>G. Cambogia</b>', body)
body = body.replace('<h3 class="normal">Bambuseæ.</h3>', '<h3 class="normal">Gramineæ</h3><p><b>Bambuseæ</b> (the bamboos, treated as a group)</p>')
toks = re.findall(r'<h2[^>]*>.*?</h2>|<h3[^>]*>.*?</h3>|<p[^>]*>.*?</p>|<li>.*?</li>|<table.*?</table>', body, flags=re.S)
def clean(t, keep_i=True):
    t = re.sub(r'<span class="pagenum">.*?</span>', '', t, flags=re.S)
    t = re.sub(r'<a class="noteref[^>]*>.*?</a>', '', t, flags=re.S)
    if keep_i:
        t = re.sub(r'<(/?)i>', r'[\1i]', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = html.unescape(t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t.replace('[i]', '<i>').replace('[/i]', '</i>')
def page(t):
    m = re.search(r'id="pb(\d+)"', t)
    return int(m.group(1)) if m else None
LABELS = {'Nom. Vulg.': 'names', 'Uses.': 'uses', 'Dose.': 'dose', 'Botanical Description.': 'botany', 'Habitat.': 'habitat'}
entries = []; group = None; family = None; fam_en = None; cur = None; sec = None; curpage = 17; stop = False
for i, t in enumerate(toks):
    if t.startswith('<h2'):
        g = clean(t, False)
        if g.startswith(('Dicot', 'Monocot')): group = g.rstrip('.')
        elif entries and not g.startswith('Medicinal'):
            break
        continue
    if t.startswith('<h3'):
        family = clean(t, False).rstrip('.'); fam_en = None
        nxt = clean(toks[i+1], False) if i+1 < len(toks) else ''
        if nxt.endswith('Family.') and len(nxt) < 60: fam_en = nxt.rstrip('.')
        continue
    p = page(t)
    m = re.match(r'<p[^>]*>\s*(?:<span class="pagenum">.*?</span>\s*)?(?:\d\.\s*)?<b>(.*?)</b>(.*)</p>', t, flags=re.S)
    look = ''.join(toks[i+1:i+5])
    if m and 'Nom. Vulg' in re.split(r'>Uses', look)[0] and 'smallcaps' not in m.group(1) and not t.startswith('<li'):
        cur = {'n': len(entries)+1, 'book_name': clean(m.group(1), False), 'book_syn': clean(m.group(2)).strip(' .'),
               'group': group, 'family': family, 'family_en': fam_en, 'page': curpage,
               'names': '', 'uses': [], 'dose': [], 'botany': [], 'habitat': []}
        entries.append(cur); sec = None
        if p: curpage = p
        continue
    if p: curpage = p
    if cur is None: continue
    m = re.match(r'<p[^>]*>\s*(?:<span class="pagenum">.*?</span>\s*)?<span class="smallcaps">(.*?)</span>\s*(.*)</p>', t, flags=re.S)
    lab = (clean(m.group(1), False).rstrip('.:—') + '.') if m else None
    if m and lab in LABELS:
        sec = LABELS[lab]
        txt = clean(m.group(2)).lstrip('.—:- ')
        if sec == 'names': cur['names'] = txt
        else: cur[sec].append(txt)
        continue
    txt = clean(t)
    if not txt or sec is None: continue
    if sec == 'names': sec = 'uses'
    if txt.endswith('Family.') and len(txt) < 60: continue
    if t.startswith('<table'): txt = '[table omitted; see the source text]'
    cur[sec].append(txt)
for i in range(len(entries)-2, -1, -1):
    e, nx = entries[i], entries[i+1]
    if not e['uses'] and not e['botany'] and not e['habitat']:
        for k in ('uses','dose','botany','habitat'): e[k] = nx[k]
        e['shared'] = nx.get('shared', []) + [nx['n']]
        if not e['names'] or e['names'].startswith('(of both)'): e['names'] = nx['names']
OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'parsed {len(entries)} entries')
