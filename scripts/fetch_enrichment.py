"""Fetch photos (Wikipedia lead image + Wikimedia Commons licence data), a name
check (GBIF backbone) and recent papers (Europe PMC) for every curated entry.
Results are cached in data/enrichment.json; delete a key to refetch it."""
import json, re, sys, time, html, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data' / 'enrichment.json'
UA = {'User-Agent': 'halamang-gamot-directory/1.0 (https://github.com/eagnespuerto/halamang-gamot-directory)'}


# Older names still common in the literature. Papers are pooled across them.
ALIASES = {
    'Vincetoxicum indicum': ['Tylophora indica', 'Tylophora asthmatica'], 'Guilandina bonduc': ['Caesalpinia bonduc', 'Caesalpinia bonducella'],
    'Biancaea sappan': ['Caesalpinia sappan'], 'Samadera indica': ['Quassia indica'],
    'Dysoxylum gaudichaudianum': ['Didymocheton gaudichaudianus'], 'Coleus amboinicus': ['Plectranthus amboinicus'],
    'Salvia rosmarinus': ['Rosmarinus officinalis'], 'Combretum indicum': ['Quisqualis indica'],
    'Vachellia farnesiana': ['Acacia farnesiana'], 'Ehretia microphylla': ['Carmona retusa'],
    'Cascabela thevetia': ['Thevetia peruviana'], 'Dysphania ambrosioides': ['Chenopodium ambrosioides'],
    'Abroma augustum': ['Abroma augusta'], 'Parkia timoriana': ['Parkia roxburghii'],
    'Catunaregam spinosa': ['Randia dumetorum', 'Randia spinosa'], 'Phyla nodiflora': ['Lippia nodiflora'],
    'Aleurites moluccanus': ['Aleurites moluccana'], 'Hymenodictyon orixense': ['Hymenodictyon excelsum'],
    'Acmella oleracea': ['Spilanthes acmella'], 'Alangium salviifolium': ['Alangium salvifolium', 'Alangium lamarckii'],
    'Ayapana triplinervis': ['Eupatorium triplinerve', 'Eupatorium ayapana'], 'Chloranthus elatior': ['Chloranthus erectus', 'Chloranthus officinalis'],
    'Trichosanthes tricuspidata': ['Trichosanthes bracteata', 'Trichosanthes palmata'], 'Bauhinia malabarica': ['Piliostigma malabaricum'],
    'Hibiscus tiliaceus': ['Talipariti tiliaceum'], 'Cleome viscosa': ['Arivela viscosa'], 'Senna alata': ['Cassia alata'],
    'Senna occidentalis': ['Cassia occidentalis'], 'Ocimum tenuiflorum': ['Ocimum sanctum'], 'Magnolia champaca': ['Michelia champaca'],
    'Lannea coromandelica': ['Odina wodier'], 'Pongamia pinnata': ['Millettia pinnata'],
    'Syzygium cumini': ['Eugenia jambolana'], 'Mallotus philippensis': ['Mallotus philippinensis'], 'Rhinacanthus nasutus': ['Rhinacanthus communis'],
    'Justicia adhatoda': ['Adhatoda vasica'], 'Anisomeles indica': ['Anisomeles ovata'], 'Manilkara zapota': ['Achras sapota'],
    'Ludwigia octovalvis': ['Jussiaea suffruticosa'], 'Centella asiatica': ['Hydrocotyle asiatica'], 'Trachyspermum ammi': ['Carum copticum'],
    'Limnophila rugosa': ['Limnophila roxburghii'], 'Tetracera scandens': ['Tetracera sarmentosa'],
    'Operculina turpethum': ['Ipomoea turpethum'], 'Citrus × aurantiifolia': ['Citrus aurantifolia'], 'Plumeria rubra': ['Plumeria acutifolia'],
    'Mentha × villosa': ['Mentha cordifolia'], 'Leucaena leucocephala': ['Leucaena glauca'], 'Citrus × microcarpa': ['Citrofortunella microcarpa', 'calamansi'],
    'Coleus scutellarioides': ['Plectranthus scutellarioides', 'Solenostemon scutellarioides', 'Coleus blumei'],
    'Kalanchoe pinnata': ['Bryophyllum pinnatum'], 'Pandanus odorifer': ['Pandanus odoratissimus'], 'Ficus caulocarpa': ['Ficus stipulosa'],
    'Brassica oleracea': ['cabbage'], 'Basella alba': ['Basella rubra'],
}


# Wikidata images that show a different species from the entry.
PHOTO_BLOCK = {'Canarium indicum - Icica icicariba - Köhler–s Medizinal-Pflanzen-171.jpg'}


# Wiki titles whose lead image is an old engraving or otherwise a poor likeness: use this Commons file instead.
PHOTO_OVERRIDE = {'Garlic': 'Garlic bulbs and cloves.jpg'}


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
        n, acc, en, fil, colors, native, wiki, note = (line.split('|') + [''] * 8)[:8]
        rows.append({'n': int(n), 'accepted': acc.strip(), 'wiki': wiki.strip()})
    return rows + ladion({r['accepted'] for r in rows})


def ladion(have):
    """Plants from the 1985 book that have no entry in curation.tsv."""
    rows = []
    for line in (ROOT / 'data' / 'ladion.tsv').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        f = [x.strip() for x in (line.split('|') + [''] * 13)[:13]]
        if f[4] not in have:
            rows.append({'n': 1000 + int(f[0]), 'accepted': f[4], 'wiki': f[11]})
    return rows


def strip(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', s or ''))).strip()


def wiki_pages(titles):
    res = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        d = get('https://en.wikipedia.org/w/api.php', {
            'action': 'query', 'format': 'json', 'redirects': 1, 'titles': '|'.join(chunk),
            'prop': 'pageimages|info|pageprops', 'piprop': 'name|original', 'pilicense': 'free',
            'inprop': 'url', 'ppprop': 'wikibase_item'}).get('query', {})
        alias = {t: t for t in chunk}
        for step in ('normalized', 'redirects'):
            m = {x['from']: x['to'] for x in d.get(step, [])}
            alias = {k: m.get(v, v) for k, v in alias.items()}
        pages = {p['title']: p for p in d.get('pages', {}).values() if 'missing' not in p}
        for t in chunk:
            p = pages.get(alias[t])
            if p:
                res[t] = {'title': p['title'], 'url': p['fullurl'], 'file': p.get('pageimage'),
                          'qid': p.get('pageprops', {}).get('wikibase_item')}
        time.sleep(0.5)
    return res


# Wikimedia serves thumbnails in fixed width steps; 330 suits cards, 960 the entry page.
def commons(files):
    res = {}
    for width, key_name in ((960, 'thumb'), (330, 'small')):
        for i in range(0, len(files), 40):
            chunk = files[i:i + 40]
            d = get('https://commons.wikimedia.org/w/api.php', {
                'action': 'query', 'format': 'json', 'titles': '|'.join('File:' + f for f in chunk),
                'prop': 'imageinfo', 'iiprop': 'url|size|extmetadata', 'iiurlwidth': width}).get('query', {})
            norm = {x['to']: x['from'] for x in d.get('normalized', [])}
            for p in d.get('pages', {}).values():
                ii = (p.get('imageinfo') or [None])[0]
                if not ii:
                    continue
                key = norm.get(p['title'], p['title'])[5:]
                em = ii.get('extmetadata', {})
                res.setdefault(key, {
                    'w': ii.get('thumbwidth'), 'h': ii.get('thumbheight'), 'page': ii.get('descriptionurl'),
                    'artist': strip(em.get('Artist', {}).get('value'))[:120],
                    'license': strip(em.get('LicenseShortName', {}).get('value')),
                    'license_url': em.get('LicenseUrl', {}).get('value', '')})[key_name] = ii.get('thumburl')
            time.sleep(0.5)
    return res


def wikidata_images(names):
    """Fallback for species with no usable Wikipedia lead image: the P18 image on the Wikidata taxon item."""
    values = ' '.join(json.dumps(n) for n in names)
    d = get('https://query.wikidata.org/sparql', {'format': 'json', 'query':
            'SELECT ?name ?img WHERE { VALUES ?name { %s } ?item wdt:P225 ?name; wdt:P18 ?img }' % values})
    out = {}
    for b in d.get('results', {}).get('bindings', []):
        out.setdefault(b['name']['value'], urllib.parse.unquote(b['img']['value'].rsplit('/', 1)[1]).replace('_', ' '))
    return out


def papers(name):
    names = [name.replace('× ', '')] + ALIASES.get(name, [])
    genera = {n.split()[0].lower() for n in names}
    for field, since in (('TITLE', 2022), ('TITLE', 2018), ('ABSTRACT', 2018)):
        terms = ' OR '.join(f'{field}:"{n}"' for n in names)
        query = f'({terms}) AND PUB_YEAR:[{since} TO 2026] AND SRC:MED'
        d = get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', {
            'format': 'json', 'pageSize': 12, 'resultType': 'lite', 'sort': 'CITED desc', 'query': query})
        out = []
        for r in d.get('resultList', {}).get('result', []):
            title = strip(r.get('title')).rstrip('.')
            types = str(r.get('pubType', '')).lower()
            if 'retract' in types or 'retract' in title.lower() or 'erratum' in types or title.lower().startswith('correction'):
                continue
            if field == 'TITLE' and not any(g in title.lower() for g in genera):
                continue
            out.append({'title': title, 'authors': r.get('authorString', '').rstrip('.'),
                        'journal': r.get('journalTitle', ''), 'year': r.get('pubYear'), 'doi': r.get('doi'),
                        'pmid': r.get('pmid'), 'cited': r.get('citedByCount', 0), 'review': 'review' in types})
        if out:
            return {'total': d.get('hitCount', 0), 'since': since, 'scope': field.lower(), 'query': query, 'items': out[:3]}
        time.sleep(0.2)
    return {'total': 0, 'since': 2018, 'scope': 'none', 'query': '', 'items': []}


def main():
    data = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    rows = [r for r in curation() if r['accepted']]
    names = sorted({r['accepted'] for r in rows})
    for nm in names:
        e = data.setdefault(nm, {})
        if 'gbif' not in e:
            g = get('https://api.gbif.org/v1/species/match', {'name': nm, 'kingdom': 'Plantae'})
            e['gbif'] = {k: g.get(k) for k in ('usageKey', 'scientificName', 'status', 'matchType', 'family', 'species')}
        if 'papers' not in e:
            e['papers'] = papers(nm)
            print('papers', nm, e['papers']['total'], e['papers']['scope'], flush=True)
            OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    # photos are keyed by wiki title because two entries can share a species but not an article
    photos = data.setdefault('_photos', {})
    want = sorted({r['wiki'] or r['accepted'] for r in rows} - set(photos))
    pages = wiki_pages(want)
    for t, f in PHOTO_OVERRIDE.items():
        if t in pages:
            pages[t]['file'] = f
    meta = commons(sorted({p['file'] for p in pages.values() if p.get('file')}))
    for t in want:
        p = pages.get(t)
        f = (p or {}).get('file') or ''
        photos[t] = None if not p else {**p, 'image': meta.get(f.replace('_', ' ')) or meta.get(f)}
    # second pass: Wikidata images for entries still without one
    lacking = {}
    for r in rows:
        t = r['wiki'] or r['accepted']
        if not (photos.get(t) or {}).get('image'):
            for nm in [r['accepted']] + ALIASES.get(r['accepted'], []):
                lacking[nm] = t
    if lacking:
        found = wikidata_images(sorted(lacking))
        meta = commons(sorted(set(found.values())))
        for nm, f in found.items():
            t = lacking[nm]
            if meta.get(f) and f not in PHOTO_BLOCK and not (photos.get(t) or {}).get('image'):
                photos[t] = {**(photos.get(t) or {'title': None, 'url': None}), 'file': f, 'image': meta[f], 'via': 'wikidata'}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    print('names', len(names), 'photo titles', len(photos))


main()
