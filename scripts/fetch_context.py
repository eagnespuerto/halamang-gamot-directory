"""Fetch a modern description and Philippine records for every curated entry.

- Description: the opening of the English Wikipedia article and, where one
  exists, of the Tagalog Wikipedia article (both CC BY-SA 4.0).
- Philippine records: GBIF occurrence counts by province (GADM level 1).

Results are cached in data/context.json; delete a key to refetch it.
"""
import json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data' / 'context.json'
UA = {'User-Agent': 'halamang-gamot-directory/1.0 (https://github.com/eagnespuerto/halamang-gamot-directory)'}


def get(url, params):
    q = urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url + '?' + q, headers=UA), timeout=40) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 + 3 * attempt)
    print('FAILED', url, params, file=sys.stderr)
    return {}


def curation():
    rows = []
    for line in (ROOT / 'data' / 'curation.tsv').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        n, acc, en, fil, colors, native, wiki, note = [x.strip() for x in (line.split('|') + [''] * 8)[:8]]
        if acc:
            rows.append({'accepted': acc, 'wiki': wiki or acc})
    have = {r['accepted'] for r in rows}
    # plants from the 1985 book that have no entry in curation.tsv
    for line in (ROOT / 'data' / 'ladion.tsv').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        f = [x.strip() for x in (line.split('|') + [''] * 13)[:13]]
        if f[4] not in have:
            rows.append({'accepted': f[4], 'wiki': f[11] or f[4]})
    return rows


def excerpt(text, limit):
    """Leading sentences of an article intro, up to about `limit` characters."""
    text = re.sub(r'\s*\(\s*[,;]?\s*\)', '', text or '')
    text = re.sub(r'[ \t]+', ' ', text).strip()
    paras = [p.strip() for p in text.split('\n') if len(p.strip()) > 40]
    out = ''
    for sentence in re.split(r'(?<=[a-z0-9\)\]][.!?])\s+(?=[A-Z"“])', ' '.join(paras)):
        if out and len(out) + len(sentence) > limit:
            break
        out = (out + ' ' + sentence).strip()
    return out


def wiki_intro(lang, title):
    d = get(f'https://{lang}.wikipedia.org/w/api.php', {
        'action': 'query', 'format': 'json', 'redirects': 1, 'titles': title,
        'prop': 'extracts|info|langlinks', 'exintro': 1, 'explaintext': 1, 'inprop': 'url',
        'lllang': 'tl', 'lllimit': 5}).get('query', {})
    for p in d.get('pages', {}).values():
        if 'missing' in p or not p.get('extract'):
            return None, None
        tl = (p.get('langlinks') or [{}])[0].get('*')
        return {'title': p['title'], 'url': p['fullurl'], 'text': p['extract']}, tl
    return None, None


def gbif_ph(name, provinces):
    m = get('https://api.gbif.org/v1/species/match', {'name': name.replace('× ', ''), 'kingdom': 'Plantae'})
    key = m.get('acceptedUsageKey') or m.get('usageKey')
    # a match that only reached the genus would count the whole genus
    if not key or (m.get('rank') != 'SPECIES' and ' ' in name):
        return None
    d = get('https://api.gbif.org/v1/occurrence/search', {
        'taxonKey': key, 'country': 'PH', 'limit': 0, 'facet': 'gadmLevel1Gid', 'facetLimit': 120})
    counts = (d.get('facets') or [{}])[0].get('counts', [])
    return {'key': key, 'total': d.get('count', 0),
            'provinces': [[provinces.get(c['name'], c['name']), c['count']] for c in counts]}


def main():
    data = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    provinces = {x['id']: x['name'] for x in get('https://api.gbif.org/v1/geocode/gadm/PHL/subdivisions', {'limit': 200})}
    for r in curation():
        e = data.setdefault(r['accepted'] + '|' + r['wiki'], {})
        if 'en' not in e:
            en, tl_title = wiki_intro('en', r['wiki'])
            e['en'] = en and {**en, 'text': excerpt(en['text'], 650)}
            tl = wiki_intro('tl', tl_title)[0] if tl_title else None
            e['tl'] = tl and {**tl, 'text': excerpt(tl['text'], 450)}
            time.sleep(0.3)
        if 'ph' not in e:
            e['ph'] = gbif_ph(r['accepted'], provinces)
            print(r['accepted'], '| en' if e['en'] else '| -', 'tl' if e['tl'] else '-', (e['ph'] or {}).get('total'), flush=True)
            OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')


main()
