"""Build the static site into docs/ from data/book.json, data/curation.tsv,
data/ladion.tsv and data/enrichment.json. No dependencies beyond the standard library.

    python scripts/build.py
"""
import html, json, re, unicodedata, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
REPO = 'https://github.com/eagnespuerto/halamang-gamot-directory'
GUTENBERG = 'https://www.gutenberg.org/cache/epub/26393/pg26393-images.html'
ARCHIVE = 'https://archive.org/details/cu31924050881592'
FETCHED = 'October 2026'

# Phosphor icons (regular weight), fetched through the better-icons MCP.
ICON_PATHS = {
    'leaf': 'M223.45 40.07a8 8 0 0 0-7.52-7.52C139.8 28.08 78.82 51 52.82 94a87.1 87.1 0 0 0-12.76 49c.57 15.92 5.21 32 13.79 47.85l-19.51 19.5a8 8 0 0 0 11.32 11.32l19.5-19.51C81 210.73 97.09 215.37 113 215.94q1.67.06 3.33.06A86.93 86.93 0 0 0 162 203.18c43-26 65.93-86.97 61.45-163.11m-69.7 149.43c-22.75 13.78-49.68 14-76.71.77l88.63-88.62a8 8 0 0 0-11.32-11.32L65.73 179c-13.19-27-13-54 .77-76.71c22.09-36.47 74.6-56.44 141.31-54.06c2.39 66.66-17.59 119.18-54.06 141.27',
    'search': 'm229.66 218.34l-50.07-50.06a88.11 88.11 0 1 0-11.31 11.31l50.06 50.07a8 8 0 0 0 11.32-11.32M40 112a72 72 0 1 1 72 72a72.08 72.08 0 0 1-72-72',
    'pin': 'M128 64a40 40 0 1 0 40 40a40 40 0 0 0-40-40m0 64a24 24 0 1 1 24-24a24 24 0 0 1-24 24m0-112a88.1 88.1 0 0 0-88 88c0 31.4 14.51 64.68 42 96.25a254.2 254.2 0 0 0 41.45 38.3a8 8 0 0 0 9.18 0a254.2 254.2 0 0 0 41.37-38.3c27.45-31.57 42-64.85 42-96.25a88.1 88.1 0 0 0-88-88m0 206c-16.53-13-72-60.75-72-118a72 72 0 0 1 144 0c0 57.23-55.47 105-72 118',
    'palette': 'M200.77 53.89A103.27 103.27 0 0 0 128 24h-1.07A104 104 0 0 0 24 128c0 43 26.58 79.06 69.36 94.17A32 32 0 0 0 136 192a16 16 0 0 1 16-16h46.21a31.81 31.81 0 0 0 31.2-24.88a104.4 104.4 0 0 0 2.59-24a103.28 103.28 0 0 0-31.23-73.23m13 93.71a15.89 15.89 0 0 1-15.56 12.4H152a32 32 0 0 0-32 32a16 16 0 0 1-21.31 15.07C62.49 194.3 40 164 40 128a88 88 0 0 1 87.09-88h.9a88.35 88.35 0 0 1 88 87.25a89 89 0 0 1-2.18 20.35ZM140 76a12 12 0 1 1-12-12a12 12 0 0 1 12 12m-44 24a12 12 0 1 1-12-12a12 12 0 0 1 12 12m0 56a12 12 0 1 1-12-12a12 12 0 0 1 12 12m88-56a12 12 0 1 1-12-12a12 12 0 0 1 12 12',
    'flask': 'M221.69 199.77L160 96.92V40h8a8 8 0 0 0 0-16H88a8 8 0 0 0 0 16h8v56.92L34.31 199.77A16 16 0 0 0 48 224h160a16 16 0 0 0 13.72-24.23Zm-110.83-96.52a7.93 7.93 0 0 0 1.14-4.11V40h32v59.14a7.93 7.93 0 0 0 1.14 4.11L183.36 167c-12 2.37-29.07 1.37-51.75-10.11c-15.91-8.05-31.05-12.32-45.22-12.81ZM48 208l28.54-47.58c14.25-1.74 30.31 1.85 47.82 10.72c19 9.61 35 12.88 48 12.88a69.9 69.9 0 0 0 19.55-2.7L208 208Z',
    'book': 'M232 48h-72a40 40 0 0 0-32 16a40 40 0 0 0-32-16H24a8 8 0 0 0-8 8v144a8 8 0 0 0 8 8h72a24 24 0 0 1 24 24a8 8 0 0 0 16 0a24 24 0 0 1 24-24h72a8 8 0 0 0 8-8V56a8 8 0 0 0-8-8M96 192H32V64h64a24 24 0 0 1 24 24v112a39.8 39.8 0 0 0-24-8m128 0h-64a39.8 39.8 0 0 0-24 8V88a24 24 0 0 1 24-24h64ZM160 88h40a8 8 0 0 1 0 16h-40a8 8 0 0 1 0-16m48 40a8 8 0 0 1-8 8h-40a8 8 0 0 1 0-16h40a8 8 0 0 1 8 8m0 32a8 8 0 0 1-8 8h-40a8 8 0 0 1 0-16h40a8 8 0 0 1 8 8',
    'right': 'm221.66 133.66l-72 72a8 8 0 0 1-11.32-11.32L196.69 136H40a8 8 0 0 1 0-16h156.69l-58.35-58.34a8 8 0 0 1 11.32-11.32l72 72a8 8 0 0 1 0 11.32',
    'left': 'M224 128a8 8 0 0 1-8 8H59.31l58.35 58.34a8 8 0 0 1-11.32 11.32l-72-72a8 8 0 0 1 0-11.32l72-72a8 8 0 0 1 11.32 11.32L59.31 120H216a8 8 0 0 1 8 8',
    'external': 'M200 64v104a8 8 0 0 1-16 0V83.31L69.66 197.66a8 8 0 0 1-11.32-11.32L172.69 72H88a8 8 0 0 1 0-16h104a8 8 0 0 1 8 8',
    'camera': 'M208 56h-27.72l-13.63-20.44A8 8 0 0 0 160 32H96a8 8 0 0 0-6.65 3.56L75.71 56H48a24 24 0 0 0-24 24v112a24 24 0 0 0 24 24h160a24 24 0 0 0 24-24V80a24 24 0 0 0-24-24m8 136a8 8 0 0 1-8 8H48a8 8 0 0 1-8-8V80a8 8 0 0 1 8-8h32a8 8 0 0 0 6.66-3.56L100.28 48h55.43l13.63 20.44A8 8 0 0 0 176 72h32a8 8 0 0 1 8 8ZM128 88a44 44 0 1 0 44 44a44.05 44.05 0 0 0-44-44m0 72a28 28 0 1 1 28-28a28 28 0 0 1-28 28',
    'translate': 'm247.15 212.42l-56-112a8 8 0 0 0-14.31 0l-21.71 43.43A88 88 0 0 1 108 126.93A103.65 103.65 0 0 0 135.69 64H160a8 8 0 0 0 0-16h-56V32a8 8 0 0 0-16 0v16H32a8 8 0 0 0 0 16h87.63A87.76 87.76 0 0 1 96 116.35a87.7 87.7 0 0 1-19-31a8 8 0 1 0-15.08 5.34A103.6 103.6 0 0 0 84 127a87.55 87.55 0 0 1-52 17a8 8 0 0 0 0 16a103.46 103.46 0 0 0 64-22.08a104.2 104.2 0 0 0 51.44 21.31l-26.6 53.19a8 8 0 0 0 14.31 7.16L148.94 192h70.11l13.79 27.58A8 8 0 0 0 240 224a8 8 0 0 0 7.15-11.58M156.94 176L184 121.89L211.05 176Z',
    'coffee': 'M80 56V24a8 8 0 0 1 16 0v32a8 8 0 0 1-16 0m40 8a8 8 0 0 0 8-8V24a8 8 0 0 0-16 0v32a8 8 0 0 0 8 8m32 0a8 8 0 0 0 8-8V24a8 8 0 0 0-16 0v32a8 8 0 0 0 8 8m96 56v8a40 40 0 0 1-37.51 39.91a96.6 96.6 0 0 1-27 40.09H208a8 8 0 0 1 0 16H32a8 8 0 0 1 0-16h24.54A96.3 96.3 0 0 1 24 136V88a8 8 0 0 1 8-8h176a40 40 0 0 1 40 40m-48-24H40v40a80.27 80.27 0 0 0 45.12 72h69.76A80.27 80.27 0 0 0 200 136Zm32 24a24 24 0 0 0-16-22.62V136a96 96 0 0 1-1.2 15a24 24 0 0 0 17.2-23Z',
    'github': 'M208.31 75.68A59.78 59.78 0 0 0 202.93 28a8 8 0 0 0-6.93-4a59.75 59.75 0 0 0-48 24h-24a59.75 59.75 0 0 0-48-24a8 8 0 0 0-6.93 4a59.78 59.78 0 0 0-5.38 47.68A58.14 58.14 0 0 0 56 104v8a56.06 56.06 0 0 0 48.44 55.47A39.8 39.8 0 0 0 96 192v8H72a24 24 0 0 1-24-24a40 40 0 0 0-40-40a8 8 0 0 0 0 16a24 24 0 0 1 24 24a40 40 0 0 0 40 40h24v16a8 8 0 0 0 16 0v-40a24 24 0 0 1 48 0v40a8 8 0 0 0 16 0v-40a39.8 39.8 0 0 0-8.44-24.53A56.06 56.06 0 0 0 216 112v-8a58.14 58.14 0 0 0-7.69-28.32M200 112a40 40 0 0 1-40 40h-48a40 40 0 0 1-40-40v-8a41.74 41.74 0 0 1 6.9-22.48a8 8 0 0 0 1.1-7.69a43.8 43.8 0 0 1 .79-33.58a43.88 43.88 0 0 1 32.32 20.06a8 8 0 0 0 6.71 3.69h32.35a8 8 0 0 0 6.74-3.69a43.87 43.87 0 0 1 32.32-20.06a43.8 43.8 0 0 1 .77 33.58a8.09 8.09 0 0 0 1 7.65a41.7 41.7 0 0 1 7 22.52Z',
    'warning': 'M236.8 188.09L149.35 36.22a24.76 24.76 0 0 0-42.7 0L19.2 188.09a23.51 23.51 0 0 0 0 23.72A24.35 24.35 0 0 0 40.55 224h174.9a24.35 24.35 0 0 0 21.33-12.19a23.51 23.51 0 0 0 .02-23.72m-13.87 15.71a8.5 8.5 0 0 1-7.48 4.2H40.55a8.5 8.5 0 0 1-7.48-4.2a7.59 7.59 0 0 1 0-7.72l87.45-151.87a8.75 8.75 0 0 1 15 0l87.45 151.87a7.59 7.59 0 0 1-.04 7.72M120 144v-40a8 8 0 0 1 16 0v40a8 8 0 0 1-16 0m20 36a12 12 0 1 1-12-12a12 12 0 0 1 12 12',
    'plant': 'M247.63 47.89a8 8 0 0 0-7.52-7.52c-51.76-3-93.32 12.74-111.18 42.22c-11.8 19.49-11.78 43.16-.16 65.74a71.3 71.3 0 0 0-14.17 27L98.33 159c7.82-16.33 7.52-33.35-1-47.49c-13.2-21.79-43.67-33.47-81.5-31.25a8 8 0 0 0-7.52 7.52c-2.23 37.83 9.46 68.3 31.25 81.5A45.8 45.8 0 0 0 63.44 176A54.6 54.6 0 0 0 87 170.33l25 25V224a8 8 0 0 0 16 0v-29.49a55.6 55.6 0 0 1 12.27-35a73.9 73.9 0 0 0 33.31 8.4a60.9 60.9 0 0 0 31.83-8.86c29.48-17.84 45.26-59.4 42.22-111.16M47.81 155.6C32.47 146.31 23.79 124.32 24 96c28.32-.24 50.31 8.47 59.6 23.81c4.85 8 5.64 17.33 2.46 26.94l-24.41-24.41a8 8 0 0 0-11.31 11.31l24.41 24.41c-9.61 3.18-18.93 2.39-26.94-2.46m149.31-10.22c-13.4 8.11-29.15 8.73-45.15 2l53.69-53.7a8 8 0 0 0-11.31-11.31L140.65 136c-6.76-16-6.15-31.76 2-45.15c13.94-23 47-35.82 89.33-34.83c.96 42.32-11.84 75.42-34.86 89.36',
    'sun': 'M120 40V16a8 8 0 0 1 16 0v24a8 8 0 0 1-16 0m72 88a64 64 0 1 1-64-64a64.07 64.07 0 0 1 64 64m-16 0a48 48 0 1 0-48 48a48.05 48.05 0 0 0 48-48M58.34 69.66a8 8 0 0 0 11.32-11.32l-16-16a8 8 0 0 0-11.32 11.32Zm0 116.68l-16 16a8 8 0 0 0 11.32 11.32l16-16a8 8 0 0 0-11.32-11.32M192 72a8 8 0 0 0 5.66-2.34l16-16a8 8 0 0 0-11.32-11.32l-16 16A8 8 0 0 0 192 72m5.66 114.34a8 8 0 0 0-11.32 11.32l16 16a8 8 0 0 0 11.32-11.32ZM48 128a8 8 0 0 0-8-8H16a8 8 0 0 0 0 16h24a8 8 0 0 0 8-8m80 80a8 8 0 0 0-8 8v24a8 8 0 0 0 16 0v-24a8 8 0 0 0-8-8m112-88h-24a8 8 0 0 0 0 16h24a8 8 0 0 0 0-16',
    'moon': 'M233.54 142.23a8 8 0 0 0-8-2a88.08 88.08 0 0 1-109.8-109.8a8 8 0 0 0-10-10a104.84 104.84 0 0 0-52.91 37A104 104 0 0 0 136 224a103.1 103.1 0 0 0 62.52-20.88a104.84 104.84 0 0 0 37-52.91a8 8 0 0 0-1.98-7.98m-44.64 48.11A88 88 0 0 1 65.66 67.11a89 89 0 0 1 31.4-26A106 106 0 0 0 96 56a104.11 104.11 0 0 0 104 104a106 106 0 0 0 14.92-1.06a89 89 0 0 1-26.02 31.4',
    'x': 'M205.66 194.34a8 8 0 0 1-11.32 11.32L128 139.31l-66.34 66.35a8 8 0 0 1-11.32-11.32L116.69 128L50.34 61.66a8 8 0 0 1 11.32-11.32L128 116.69l66.34-66.35a8 8 0 0 1 11.32 11.32L139.31 128Z',
}


def icon(name, cls='icon'):
    return f'<svg class="{cls}" viewBox="0 0 256 256" aria-hidden="true" focusable="false"><path fill="currentColor" d="{ICON_PATHS[name]}"/></svg>'


COLORS = {
    'white': ('#f6f6f0', 'white'), 'cream': ('#f0e3b4', 'white'), 'greenish-white': ('#dfe8c6', 'white'),
    'yellow': ('#f0be28', 'yellow'), 'greenish-yellow': ('#c6cc4e', 'yellow'), 'orange': ('#ea8527', 'orange'),
    'red': ('#cb3226', 'red'), 'scarlet': ('#e03a1e', 'red'), 'crimson': ('#9f1730', 'red'),
    'pink': ('#ee9ab3', 'pink'), 'magenta': ('#c0338a', 'pink'), 'lilac': ('#c0a4de', 'purple'),
    'purple': ('#7a3f9e', 'purple'), 'violet': ('#6a4cc2', 'purple'), 'blue': ('#3f6fd0', 'blue'),
    'green': ('#5c9a48', 'green'), 'brown': ('#8a5a36', 'brown'), 'black': ('#27231f', 'brown'), 'grey': ('#9aa19f', 'brown'),
}
COLOR_GROUPS = ['white', 'yellow', 'orange', 'red', 'pink', 'purple', 'blue', 'green', 'brown']
GROUP_HEX = {'white': '#f6f6f0', 'yellow': '#f0be28', 'orange': '#ea8527', 'red': '#cb3226', 'pink': '#ee9ab3',
             'purple': '#7a3f9e', 'blue': '#3f6fd0', 'green': '#5c9a48', 'brown': '#8a5a36'}
GROUP_LABEL = {'brown': 'brown or dark'}
LANGS = [('Tag.', 'Tagalog'), ('Vis.', 'Visayan'), ('Pam.', 'Pampango'), ('Iloc.', 'Ilocano'), ('Bic.', 'Bicol'),
         ('Pan.', 'Pangasinan'), ('Sp.', 'Spanish'), ('Sp.-Fil.', 'Spanish as used in the Philippines'),
         ('Eng.', 'English'), ('Indo-Eng.', 'English as used in India')]


LADION = 'Healing Wonders of Herbs'

# Ailment groups for the home page filter: key, label, words to look for in the 1901 book's "Uses" text,
# and the chapter titles of the 1985 book that fall under the group.
AILMENTS = [
    ('fever', 'Fever', r'\bfevers?\b|febrifuge|antipyretic|antiperiodic|malaria', ['fever']),
    ('cough', 'Cough and asthma', r'cough|asthma|bronchi|expectorant|catarrh|phthisis|pectoral', ['cough', 'asthma']),
    ('mouth', 'Mouth, teeth and throat',
     r'sore throat|gargle|toothache|\bgums\b|aphth|mouth-?wash|tonsil|odontalg|stomatitis|\bteeth\b|thrush',
     ['sore throat', 'swollen gums and mouth inflammation', 'toothache']),
    ('diarrhea', 'Diarrhea and dysentery', r'diarrh|dysenter', ['diarrhea']),
    ('stomach', 'Stomach and digestion', r'dyspeps|indigestion|flatulen|carminative|stomachic|\bcolic|gastr|digestion',
     ['indigestion', 'flatulence or gas pain', 'hyperacidity']),
    ('constipation', 'Constipation', r'constipat|purgative|laxative|cathartic|\bpurge', ['constipation']),
    ('worms', 'Worms', r'anthelmintic|vermifuge|t[aæ]nia|tape-?worm|lumbric|\bworms\b|ascari', ['worm infestation']),
    ('skin', 'Skin', r'skin diseases?|(?:diseases|affections|eruptions) of the skin|cutaneous|eczema|herpe|\bitch|scabies|ringworm'
                     r'|lepro|psoriasis|dermat',
     ['eczema', 'ringworm', 'scabies', 'skin eruptions and dermatitis', 'skin itchiness and allergy', 'herpes', "athlete's foot",
      'sunburn and prickly heat', 'pimples or acne', 'measles and/or skin rashes', 'chicken pox', 'underarm body odor']),
    ('wounds', 'Wounds, burns and boils', r'\bwounds?\b|\bburns\b|scalds?\b|\bboils?\b|abscess|\bulcers?\b|h[æe]mostatic|\bsores?\b',
     ['bleeding wound', 'burns', 'abscesses and boils']),
    ('pain', 'Joint pain, sprains and swelling', r'rheumati|sprain|contusion|bruise|neuralgi|lumbago|\bgout|swelling',
     ['rheumatism or rheumatic joint pain', 'sprained ankle or wrist', 'mumps']),
    ('head', 'Headache and fainting', r'headache|cephalalgia|migraine|fainting|syncope|vertigo',
     ['headaches due to sinusitis', 'fainting spells']),
    ('urinary', 'Urinary', r'diuretic|urinar|cystitis|bladder|calculi|calculus|dysuria|nephrit|dropsy', ['acute and chronic cystitis']),
    ('hemorrhoids', 'Hemorrhoids', r'h[æe]morrhoid|\bpiles\b', ['hemorrhoids']),
    ('bites', 'Bites and stings', r'snake|\bbites?\b|\bstings?\b|scorpion|venom|centipede',
     ['snake bites', 'bee and wasp stings', 'mosquito bites']),
    ('hair', 'Hair and scalp', r'dandruff|\blice\b|pedicul|\bhair\b|scalp|alopecia|baldness', ['dandruff', 'lice infestation on the head']),
    ('women', 'Menstruation and childbirth',
     r'menstru|emmenagogue|amenorrh|dysmenorrh|leucorrh|parturition|childbirth|uterine|galactagogue|lochia', []),
    ('eyes', 'Eyes and ears', r'ophthalm|conjunctiv|\beyes?\b|otitis|otorrh|earache|\bears?\b|collyrium', []),
]
AILMENT_LABEL = {k: label for k, label, _, _ in AILMENTS}
CHAPTER_GROUP = {ch: k for k, _, _, chapters in AILMENTS for ch in chapters}


def tag_ailments(p):
    """Ailment groups for one plant: keyword matches in the 1901 text, chapter titles from the 1985 book."""
    text = plain(' '.join(p['uses'])).lower()
    keys = {k for k, _, pattern, _ in AILMENTS if text and re.search(pattern, text)}
    for ailment, how, _, _ in (p['ladion'] or {}).get('uses', []):
        keys.add('fever' if how.endswith('for the fever') else CHAPTER_GROUP[ailment])
    return [k for k, _, _, _ in AILMENTS if k in keys]


def load_ladion():
    rows = []
    for line in (ROOT / 'data' / 'ladion.tsv').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        n, pg, title, printed, acc, en, fil, names, uses, colors, native, wiki, note = [
            x.strip() for x in (line.split('|') + [''] * 13)[:13]]
        rows.append(dict(
            n=int(n), page=int(pg), title=title, printed=printed, accepted=acc, english=en, filipino=fil, colors=colors,
            native=native, wiki=wiki, note=note,
            names=[tuple(x.strip() for x in chunk.split(':', 1)) for chunk in names.split(';') if chunk.strip()],
            uses=[(a.strip(), how.strip(), dose or '', int(pg2)) for a, how, dose, pg2 in
                  (re.match(r'(.*?)=(.*?)(?:\s*\{(.*)\})?@(\d+)$', chunk.strip()).groups()
                   for chunk in uses.split(';') if chunk.strip())]))
    return rows


def esc(s):
    return html.escape(s or '', quote=True)


def rich(s):
    """Escape book text while keeping the italics the parser preserved."""
    return esc(s).replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')


def plain(s):
    return re.sub(r'<[^>]+>', '', s or '')


def fold(s):
    s = unicodedata.normalize('NFKD', plain(s))
    return re.sub(r'\s+', ' ', ''.join(c for c in s if not unicodedata.combining(c)).lower()).strip()


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', fold(s).replace('×', '')).strip('-')


def load():
    book = json.loads((ROOT / 'data' / 'book.json').read_text(encoding='utf-8'))
    enrich = json.loads((ROOT / 'data' / 'enrichment.json').read_text(encoding='utf-8'))
    photos = enrich['_photos']
    context = json.loads((ROOT / 'data' / 'context.json').read_text(encoding='utf-8'))
    powo_text = json.loads((ROOT / 'data' / 'powo_descriptions.json').read_text(encoding='utf-8'))
    other_names = json.loads((ROOT / 'data' / 'other_names.json').read_text(encoding='utf-8'))
    extra = json.loads((ROOT / 'data' / 'extra_photos.json').read_text(encoding='utf-8'))
    cur = {}
    for line in (ROOT / 'data' / 'curation.tsv').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        n, acc, en, fil, colors, native, wiki, note = [x.strip() for x in (line.split('|') + [''] * 8)[:8]]
        cur[int(n)] = dict(accepted=acc, english=en, filipino=fil, colors=colors, native=native, wiki=wiki, note=note)
    # Plants of the 1985 book join the entry for the same species, or get an entry of their own after the 1901 ones.
    ladion = {row['accepted']: row for row in load_ladion()}
    have = {c['accepted'] for c in cur.values()}
    for row in ladion.values():
        if row['accepted'] not in have:
            n = len(book) + 1
            book.append({'n': n, 'book_name': row['accepted'], 'book_syn': '', 'group': None, 'family': '', 'family_en': None,
                         'page': None, 'names': '', 'uses': [], 'dose': [], 'botany': [], 'habitat': [], 'tavera': False})
            cur[n] = {k: row[k] for k in ('accepted', 'english', 'filipino', 'colors', 'native', 'wiki')} | {'note': ''}
    plants, genus, seen = [], '', {}
    for e in book:
        c = cur[e['n']]
        # "A. reticulata, L." -> name + authority, expanding the abbreviated genus
        raw = re.sub(r'^\d+\.\s*', '', e['book_name']).strip()
        name, _, auth = raw.partition(',')
        name = name.strip()
        if re.match(r'^[A-Z]\.\s', name):
            name = genus + name[2:]
        else:
            genus = name.split()[0]
        name = name.replace('reticulate', 'reticulata')
        printed_rest = (auth.strip() + ' ' + e['book_syn'].strip()).strip().lstrip(', ').strip()
        printed_rest = re.sub(r'\s+', ' ', printed_rest)
        if printed_rest and not printed_rest.endswith(('.', ')')):
            printed_rest += '.'
        p = dict(e, **c)
        p['tavera'] = e.get('tavera', True)
        p['ladion'] = ladion.pop(c['accepted'], None) if c['accepted'] else None
        p['ailments'] = tag_ailments(p)
        p['printed'] = name
        p['printed_rest'] = printed_rest
        p['sci'] = c['accepted'] or name
        p['title'] = c['filipino'] or c['english'] or p['sci']
        p['subtitle'] = c['english'] if c['filipino'] and fold(c['english']) != fold(c['filipino']) else ''
        base = slugify(p['sci'])
        if base in seen:
            base = f"{base}-{slugify(c['english'] or name)}"
        seen[base] = 1
        p['slug'] = base
        en = enrich.get(c['accepted'], {}) if c['accepted'] else {}
        p['papers'] = en.get('papers', {'items': [], 'total': 0, 'since': 2022, 'query': ''})
        p['modern_family'] = (en.get('gbif') or {}).get('family') or ''
        ph = photos.get(c['wiki'] or c['accepted']) if c['accepted'] else None
        p['wiki_url'] = (ph or {}).get('url')
        p['photo'] = (ph or {}).get('image')
        if p['photo']:
            for k in ('thumb', 'small'):
                p['photo'][k] = (p['photo'].get(k) or '').split('?')[0]
        elif c['accepted'] in extra:
            # Nothing on Wikimedia Commons: an iNaturalist photo, or failing that a Kew herbarium sheet
            k = extra[c['accepted']]
            if k['source'] == 'powo':
                p['photo'] = {'thumb': k['thumb'], 'small': k['small'], 'w': None, 'h': None, 'specimen': True,
                              'page': 'https://powo.science.kew.org/taxon/' + k['taxon'],
                              'artist': 'Board of Trustees, RBG Kew', 'license': 'CC BY 3.0',
                              'license_url': 'https://creativecommons.org/licenses/by/3.0/'}
            else:
                p['photo'] = dict(k, w=None, h=None, via='iNaturalist')
        ctx = context.get(f"{c['accepted']}|{c['wiki'] or c['accepted']}", {}) if c['accepted'] else {}
        p['about_en'], p['about_tl'], p['ph'] = ctx.get('en'), ctx.get('tl'), ctx.get('ph')
        p['about_powo'] = powo_text.get(c['accepted']) if not p['about_en'] else None
        p['other_names'] = other_names.get(c['accepted']) if c['accepted'] else None
        p['swatches'], p['color_source'] = parse_colors(c['colors'], e)
        groups = [COLORS[col][1] for part, cols in p['swatches'] if part == 'flower' for col in cols]
        if not groups:
            groups = [COLORS[col][1] for part, cols in p['swatches'] for col in cols]
        p['groups'] = sorted(set(groups), key=COLOR_GROUPS.index)
        plants.append(p)
    by_n = {p['n']: p for p in plants}
    for p in plants:
        p['shared_with'] = [by_n[n] for n in p.get('shared', [])]
        p['described_with'] = [q for q in plants if p['n'] in q.get('shared', [])]
    return plants


def parse_colors(spec, entry):
    out = []
    for chunk in filter(None, (x.strip() for x in spec.split(';'))):
        part, _, cols = chunk.partition('=')
        out.append((part.strip(), [c.strip() for c in cols.split(',') if c.strip() in COLORS]))
    if out:
        return out, 'curated'
    # No curated colours: read the flower colour out of the book's own description.
    text = plain(' '.join(entry['botany'])).lower()
    found = []
    for sentence in re.split(r'(?<=[.;])\s', text):
        if re.search(r'\b(flower|corolla|petal)', sentence):
            for col in COLORS:
                if re.search(rf'\b{col}\b', sentence) and col not in found:
                    found.append(col)
    return ([('flower', found)] if found else []), 'book'


# ---------- shared page chrome ----------

def page(title, desc, body, depth=0, active='', extra_head=''):
    up = '../' * depth
    nav = ''.join(
        f'<a href="{up}{href}"{" aria-current=\"page\"" if key == active else ""}>{label}</a>'
        for key, href, label in (('plants', 'index.html', 'Plants'), ('families', 'families.html', 'Families'),
                                 ('about', 'about.html', 'About the books')))
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="color-scheme" content="light dark">
<script>try{{var t=localStorage.getItem('theme');if(t==='light'||t==='dark')document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<link rel="preload" href="{up}assets/fonts/hanken-grotesk-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{up}assets/fonts/newsreader-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{up}assets/site.css">
<link rel="icon" href="{up}assets/favicon.svg" type="image/svg+xml">
{extra_head}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap bar">
    <a class="brand" href="{up}index.html">{icon('leaf')}<span>Halamang Gamot Directory</span></a>
    <nav aria-label="Main">{nav}</nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap footer-row">
    <div class="footer-text">
    <p>Halamang Gamot Directory is an open, static guide to two Philippine books on medicinal plants. Every entry links to its sources; if you spot an error, <a href="{REPO}/issues" target="_blank" rel="noopener">open an issue on GitHub</a>.</p>
    <p>Icons by <a href="https://phosphoricons.com" target="_blank" rel="noopener">Phosphor Icons</a> (MIT). The 1901 book's text is in the public domain. The 1985 book is in copyright, so its entries are summaries. Modern descriptions are excerpts from Wikipedia under CC BY-SA 4.0. Photos keep their own licences, credited on each entry. Site code MIT licensed.</p>
    <p>Built by Ella Puerto with the help of Claude Code. <a href="https://ko-fi.com/eagnespuerto" target="_blank" rel="noopener">{icon('coffee')} Support on Ko-fi</a></p>
    </div>
    <button type="button" class="theme-toggle" id="theme-toggle" hidden>
      <span class="when-light">{icon('moon')} Dark mode</span>
      <span class="when-dark">{icon('sun')} Light mode</span>
    </button>
  </div>
</footer>
<script src="{up}assets/theme.js" defer></script>
</body>
</html>
'''


def swatch(col):
    return f'<span class="swatch" style="--c:{COLORS[col][0]}" title="{col}"></span>'


def card(p, up=''):
    if p['photo']:
        ph = p['photo']
        size = f' width="330" height="{round(330 * ph["h"] / ph["w"])}"' if ph['w'] else ''
        img = f'<img src="{esc(ph["small"])}" alt="" loading="lazy" decoding="async"{size}>'
    else:
        img = f'<span class="no-photo">{icon("plant")}</span>'
    dots = ''.join(swatch(c) for part, cols in p['swatches'][:1] for c in cols)
    lad = p['ladion'] or {}
    q = fold(' '.join([p['title'], p['english'], p['sci'], p['printed'], p['names'], p['family'], p['modern_family'],
                       lad.get('title', ''), lad.get('printed', ''), ' '.join(v for _, v in lad.get('names', []))]))
    src = ' '.join(k for k, on in (('1901', p['tavera']), ('1985', p['ladion'])) if on)
    return (f'<li class="card" data-q="{esc(q)}" data-colors="{" ".join(p["groups"])}" data-n="{p["n"]}" '
            f'data-ailments="{" ".join(p["ailments"])}" data-src="{src}" '
            f'data-name="{esc(fold(p["title"]))}" data-sci="{esc(fold(p["sci"]))}">'
            f'<a href="{up}plants/{p["slug"]}.html"><span class="thumb">{img}</span>'
            f'<span class="card-body"><span class="card-title">{esc(p["title"])}</span>'
            f'<span class="card-sci"><i>{esc(p["sci"])}</i></span>'
            f'<span class="card-meta">{esc(p["subtitle"])}<span class="dots">{dots}</span></span></span></a></li>')


# ---------- pages ----------

def build_index(plants):
    featured = [next(p for p in plants if p['sci'] == s) for s in ('Jasminum sambac', 'Vitex negundo', 'Blumea balsamifera')]
    hero_photos = ''.join(
        f'<a class="hero-photo hero-photo-{i}" href="plants/{p["slug"]}.html">'
        f'<img src="{esc(p["photo"]["thumb" if i == 0 else "small"])}" alt="{esc(p["title"])} ({esc(p["sci"])})" '
        f'width="{p["photo"]["w"]}" height="{p["photo"]["h"]}" {"fetchpriority=\"high\"" if i == 0 else ""}>'
        f'<span>{esc(p["title"])}</span></a>'
        for i, p in enumerate(featured))
    chips = ''.join(
        f'<button type="button" class="chip" data-color="{g}" aria-pressed="false">'
        f'<span class="swatch" style="--c:{GROUP_HEX[g]}"></span>{GROUP_LABEL.get(g, g)}</button>' for g in COLOR_GROUPS)
    cards = ''.join(card(p) for p in plants)
    specimens = sum(1 for p in plants if p['photo'] and p['photo'].get('specimen'))
    inat = sum(1 for p in plants if p['photo'] and p['photo'].get('via') == 'iNaturalist')
    with_photo = sum(1 for p in plants if p['photo']) - specimens - inat
    with_papers = sum(1 for p in plants if p['papers']['items'])
    n_tavera = sum(1 for p in plants if p['tavera'])
    n_ladion = sum(1 for p in plants if p['ladion'])
    n_both = sum(1 for p in plants if p['tavera'] and p['ladion'])
    ailment_options = ''.join(
        f'<option value="{k}">{label} ({sum(1 for p in plants if k in p["ailments"])})</option>' for k, label, _, _ in AILMENTS)
    body = f'''<section class="hero">
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <h1>Browse {len(plants)} healing plants recorded in Philippine books of herbs.</h1>
      <p class="lede">Drawn from T. H. Pardo de Tavera's <i>The Medicinal Plants of the Philippines</i> (1901) and Herminia de Guzman-Ladion's <i>{LADION}</i> (1985), laid out one plant per page with today's names, the ailments each was used for, flower colours, native range, a photo and recent research.</p>
      <form class="search" role="search" onsubmit="return false">
        <label class="sr-only" for="q">Search plants</label>
        {icon('search')}
        <input id="q" type="search" placeholder="Try lagundi, Moringa or Malvaceae" autocomplete="off">
      </form>
    </div>
    <div class="hero-photos">{hero_photos}</div>
  </div>
</section>
<section class="wrap directory" aria-labelledby="dir-h">
  <div class="dir-head">
    <h2 id="dir-h">All plants</h2>
    <p class="count" id="count" aria-live="polite">{len(plants)} entries</p>
  </div>
  <div class="filters">
    <div class="chips" role="group" aria-label="Flower colour"><span class="filters-label">{icon('palette')} Flower colour</span>{chips}</div>
    <div class="selects">
      <label class="sort">Ailment
        <select id="ailment">
          <option value="">Any ailment</option>
          {ailment_options}
        </select>
      </label>
      <label class="sort">Source
        <select id="source">
          <option value="">Both books ({len(plants)})</option>
          <option value="1901">1901, Pardo de Tavera ({n_tavera})</option>
          <option value="1985">1985, de Guzman-Ladion ({n_ladion})</option>
        </select>
      </label>
      <label class="sort">Sort
        <select id="sort">
          <option value="n">Book order</option>
          <option value="name">Common name A to Z</option>
          <option value="sci">Scientific name A to Z</option>
        </select>
      </label>
    </div>
  </div>
  <ul class="grid" id="grid">{cards}</ul>
  <p class="empty" id="empty" hidden>No plant matches that search. Try a shorter word, or clear the ailment, source and colour filters.</p>
</section>
<section class="wrap coverage">
  <h2>What each entry holds</h2>
  <div class="coverage-grid">
    <p class="coverage-lead">{n_tavera} plants come from the 1901 book, quoted in its own words on uses, dose, botany and habitat. {n_ladion} come from the 1985 book, {n_both} of them plants the older book also covers, with its remedies summarised by ailment. Both sit beside facts gathered in {FETCHED}. {with_photo} of {len(plants)} entries have a photo from Wikimedia Commons, {inat} from iNaturalist, {specimens} show a herbarium sheet from Kew, and {with_papers} list papers from Europe PMC.</p>
    <dl class="coverage-list">
      <div><dt>{icon('translate')} Names</dt><dd>The Tagalog, Visayan, Ilocano, Spanish and English names each book recorded, plus the name in use today.</dd></div>
      <div><dt>{icon('leaf')} Ailments</dt><dd>What each book used the plant for, grouped so the list above can be filtered by ailment.</dd></div>
      <div><dt>{icon('plant')} Description</dt><dd>A modern account from Wikipedia in English and, where one exists, in Tagalog.</dd></div>
      <div><dt>{icon('pin')} Location</dt><dd>Where the plant is native, where the 1901 book says it grew, and which Philippine provinces have records of it today.</dd></div>
      <div><dt>{icon('flask')} Research</dt><dd>The most cited recent papers with the plant in the title, linked to the publisher.</dd></div>
    </dl>
  </div>
  <p class="caution">{icon('warning')}<span>The remedies and doses are a historical record from 1901 and 1985. Several of these plants are poisonous. Do not treat this site as medical advice.</span></p>
</section>
<script src="assets/site.js" defer></script>'''
    desc = (f"A browsable directory of {len(plants)} medicinal plants from Pardo de Tavera's The Medicinal Plants of the Philippines (1901) "
            f"and de Guzman-Ladion's {LADION} (1985), with modern names, ailments, colours, native range, photos and recent research.")
    (DOCS / 'index.html').write_text(page('Halamang Gamot Directory', desc, body, active='plants'), encoding='utf-8')


def paper_html(it):
    url = f'https://doi.org/{it["doi"]}' if it.get('doi') else f'https://europepmc.org/article/MED/{it["pmid"]}'
    authors = it.get('authors') or ''
    first = authors.split(',')[0].strip()
    who = f'{first} and others' if ',' in authors else first
    meta = ', '.join(x for x in (who, f'<i>{esc(it.get("journal") or "")}</i>' if it.get('journal') else '', str(it.get('year') or '')) if x)
    tag = '<span class="tag">Review</span>' if it.get('review') else ''
    return (f'<li><a href="{esc(url)}" target="_blank" rel="noopener">{rich(re.sub(r"</?(?!i>)[^>]*>", "", it["title"]))}'
            f'{icon("external")}</a><span class="paper-meta">{meta} {tag}</span></li>')


def today_html(p):
    """Modern description (Wikipedia in English and Tagalog, or POWO) and Philippine records from GBIF."""
    by_sa = '<a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a>'
    parts = []
    if p['about_en']:
        a = p['about_en']
        parts.append(f'<p>{esc(a["text"])}</p><p class="credit">Excerpt from <a href="{esc(a["url"])}" target="_blank" '
                     f'rel="noopener">“{esc(a["title"])}” on Wikipedia</a>, {by_sa}.</p>')
    elif p['about_powo']:
        a = p['about_powo']
        parts.append(f'<p>{esc(a["text"])}</p><p class="credit">From <a href="https://powo.science.kew.org/taxon/{a["taxon"]}" '
                     f'target="_blank" rel="noopener">Plants of the World Online</a>, Royal Botanic Gardens, Kew, '
                     f'<a href="https://creativecommons.org/licenses/by/3.0/" target="_blank" rel="noopener">CC BY 3.0</a>.</p>')
    if p['about_tl']:
        a = p['about_tl']
        parts.append(f'<h3>Sa Tagalog</h3><p lang="tl">{esc(a["text"])}</p><p class="credit" lang="tl">Sipi mula sa '
                     f'<a href="{esc(a["url"])}" target="_blank" rel="noopener">“{esc(a["title"])}” sa Tagalog Wikipedia</a>, {by_sa}.</p>')
    if not parts:
        parts.append('<p>No openly licensed description of this plant was found.</p>')
    ph = p['ph']
    if ph:
        link = f'https://www.gbif.org/occurrence/search?taxon_key={ph["key"]}&amp;country=PH'
        parts.append('<h3>Recorded in the Philippines</h3>')
        if ph['total']:
            provs = ph['provinces']
            top = ', '.join(f'{esc(n)} ({c})' for n, c in provs[:8])
            rest = len(provs) - 8
            where = ''
            if provs:
                where = (f' The ones with map coordinates fall in {len(provs)} province{"s" if len(provs) != 1 else ""}'
                         f'{", most often " if rest > 0 else ": "}{top}{f", and {rest} more" if rest > 0 else ""}.')
            parts.append(f'<p>GBIF holds {ph["total"]:,} record{"s" if ph["total"] != 1 else ""} of this plant from the Philippines.{where}</p>')
            parts.append(f'<p class="credit">Counts from <a href="{link}" target="_blank" rel="noopener">GBIF occurrence records</a>, '
                         f'{FETCHED}. They include planted trees and garden plants, and a province with no records may only lack collectors.</p>')
        else:
            parts.append(f'<p>GBIF holds no records of this plant from the Philippines.</p><p class="credit">Checked against '
                         f'<a href="{link}" target="_blank" rel="noopener">GBIF occurrence records</a>, {FETCHED}.</p>')
    return f'''<section class="today" aria-labelledby="td-h">
  <h2 id="td-h">{icon('plant')} The plant today</h2>
  <div class="prose">{''.join(parts)}</div>
</section>'''


def build_plant(p, prev, nxt):
    up = '../'
    # header
    printed = f'<i>{esc(p["printed"])}</i>{", " + rich(p["printed_rest"]) if p["printed_rest"] else ""}'
    family_bits = [esc(p['modern_family'])] if p['modern_family'] else []
    if p['tavera'] and fold(p['family']).replace('ae', 'e') != fold(p['modern_family']).replace('ae', 'e'):
        family_bits.append(f'filed in the book under {esc(p["family"])}')
    head = f'''<header class="plant-head wrap">
  <a class="back" href="{up}index.html">{icon('left')} All plants</a>
  <h1>{esc(p['title'])}</h1>
  <p class="sci"><i>{esc(p['sci'])}</i>{' · ' + esc(p['subtitle']) if p['subtitle'] else ''}</p>
</header>'''
    # photo
    if p['photo']:
        ph = p['photo']
        lic = (f'<a href="{esc(ph["license_url"])}" target="_blank" rel="noopener">{esc(ph["license"])}</a>'
               if ph.get('license_url') else esc(ph.get('license') or 'see file page'))
        if ph.get('specimen'):
            figure = f'''<figure class="plant-photo plant-photo-specimen">
  <img src="{esc(ph['thumb'])}" alt="Pressed herbarium specimen of {esc(p['sci'])}" fetchpriority="high">
  <figcaption>{icon('camera')}<span>Herbarium specimen at Kew. Digital image © {esc(ph['artist'])}, {lic}, via <a href="{esc(ph['page'])}" target="_blank" rel="noopener">Plants of the World Online</a></span></figcaption>
</figure>'''
        else:
            figure = f'''<figure class="plant-photo">
  <img src="{esc(ph['thumb'])}" alt="{esc(p['title'])}, {esc(p['sci'])}"{f' width="{ph["w"]}" height="{ph["h"]}"' if ph['w'] else ''} fetchpriority="high">
  <figcaption>{icon('camera')}<span>Photo: {esc(ph.get('artist') or 'see file page')}, {lic}, via <a href="{esc(ph['page'])}" target="_blank" rel="noopener">{ph.get('via') or 'Wikimedia Commons'}</a></span></figcaption>
</figure>'''
    else:
        figure = f'''<figure class="plant-photo plant-photo-none">
  <div class="no-photo">{icon('plant')}</div>
  <figcaption><span>No freely licensed photo of this species was found on Wikimedia Commons.</span></figcaption>
</figure>'''
    # facts
    rows = []
    # The book writes "(?)", "Not known." or "Doubtful." where it had no local name to give.
    names = re.sub(r'^\(\?\)[.;]?\s*', '', p['names']).strip()
    no_local = names != p['names'].strip() or plain(names).rstrip('.').lower() in ('', 'not known', 'unknown', 'doubtful')
    lad = p['ladion']
    if not p['tavera']:
        pass
    elif no_local:
        named = '' if plain(names).rstrip('.').lower() in ('', 'not known', 'unknown', 'doubtful') else rich(names) + ' '
        rows.append(('translate', 'Names in the book', named + 'The book records no Philippine name for this plant.'))
        other = p['other_names'] or {}

        def cite(pairs):
            return ' and '.join(f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(label)}</a>' for label, u in pairs)
        if other.get('names'):
            gloss = f' {esc(other["gloss"])}' if other.get('gloss') else ''
            rows.append(('translate', 'Names from other sources',
                         f'{other["names"]}.{gloss}<span class="fine"> Listed by {cite(other["sources"])}.</span>'))
        elif other.get('checked'):
            rows.append(('translate', 'Names from other sources',
                         f'None found. {cite(other["checked"])} gives names from neighbouring countries but none from the Philippines.'))
    elif names:
        rows.append(('translate', 'Names in the 1901 book' if lad else 'Names in the book', rich(names)))
    if lad:
        listed = '; '.join(f'{esc(lang)}: <i>{esc(vals)}</i>' for lang, vals in lad['names'])
        rows.append(('translate', 'Names in the 1985 book' if p['tavera'] else 'Names in the book', listed))
    if p['ailments']:
        links = ''.join(f'<a class="ailment" href="{up}index.html?ailment={k}">{AILMENT_LABEL[k]}</a>' for k in p['ailments'])
        rows.append(('leaf', 'Used for', f'<span class="ailments">{links}</span>'))
    if p['swatches']:
        parts = ''.join(
            f'<span class="color-part"><span class="part">{esc(part)}</span>{"".join(swatch(c) for c in cols)}'
            f'<span class="color-names">{esc(", ".join(cols))}</span></span>' for part, cols in p['swatches'] if cols)
        src = '' if p['color_source'] == 'curated' else '<span class="fine">Read from the book\'s description.</span>'
        rows.append(('palette', 'Colours', f'<span class="colors">{parts}</span>{src}'))
    if p['native']:
        rows.append(('pin', 'Native range', esc(p['native'])))
    # Long habitat passages run into botany, so the panel takes the opening lines and the full text goes below.
    habitat = ' '.join(p['habitat'])
    long_habitat = len(plain(habitat)) > 200
    if habitat:
        short = habitat
        if long_habitat:
            sentences = re.split(r'(?<=[a-z]\.)\s+(?=[A-Z])', p['habitat'][0])
            short = ' '.join(sentences[:2]) if len(plain(' '.join(sentences[:2]))) <= 200 else sentences[0]
        rows.append(('pin', 'In the Philippines, per the book', rich(short)))
    if family_bits:
        rows.append(('plant', 'Family', ', '.join(family_bits)))
    src_links = []
    if p['tavera']:
        src_links.append(f'<a href="{GUTENBERG}#pb{p["page"]}" target="_blank" rel="noopener">Page {p["page"]} on Project Gutenberg</a>')
        rows.append(('book', 'Printed in 1901 as' if lad else 'Printed as', printed))
    if lad:
        src_links.append(f'<i>{LADION}</i> (1985), page {lad["page"]}')
        rows.append(('book', 'Printed in 1985 as' if p['tavera'] else 'Printed as', f'<i>{esc(lad["printed"])}</i>'))
    if p['wiki_url']:
        src_links.append(f'<a href="{esc(p["wiki_url"])}" target="_blank" rel="noopener">Wikipedia</a>')
    rows.append(('external', 'Sources', ' · '.join(src_links)))
    facts = '<dl class="facts">' + ''.join(
        f'<div><dt>{icon(ic)}{label}</dt><dd>{val}</dd></div>' for ic, label, val in rows) + '</dl>'
    note = f'<p class="note">{icon("leaf")}<span>{esc(p["note"])}</span></p>' if p['note'] else ''
    # book text
    def block(title, paras):
        if not paras:
            return ''
        return f'<h3>{title}</h3>' + ''.join(f'<p>{rich(t)}</p>' for t in paras)
    shared = ''
    others = p['shared_with'] or p['described_with']
    if others:
        links = ' and '.join(f'<a href="{o["slug"]}.html">{esc(o["title"])} (<i>{esc(o["printed"])}</i>)</a>' for o in others)
        shared = f'<p class="fine">The book gives one account for this plant and {links}, so the text below appears on each page.</p>'
    book_text = (block('Uses', p['uses']) + block('Dose', p['dose']) + block('Botanical description', p['botany'])
                 + (block('Habitat', p['habitat']) if long_habitat else ''))
    if not book_text:
        book_text = '<p>The book lists this plant by name only.</p>'
    text = f'''<section class="book-text" aria-labelledby="bt-h">
  <h2 id="bt-h">{icon('book')} What the 1901 book says</h2>
  <p class="caution">{icon('warning')}<span>A historical record, quoted as printed. Doses and remedies here are not medical advice.</span></p>
  {shared}
  <div class="prose">{book_text}</div>
</section>''' if p['tavera'] else ''
    if lad:
        remedies = ''.join(
            f'<li><b>{esc(a[0].upper() + a[1:])}</b><span>{esc(how[0].upper() + how[1:])}.</span>'
            f'{f"<span class=dose>{esc(dose)}.</span>" if dose else ""}<span class="fine">Page {pg}</span></li>'
            for a, how, dose, pg in lad['uses'])
        lad_note = f'<p class="note">{icon("leaf")}<span>{esc(lad["note"])}</span></p>' if lad['note'] else ''
        text += f'''<section class="book-text" aria-labelledby="lw-h">
  <h2 id="lw-h">{icon('book')} What the 1985 book uses it for</h2>
  <p class="caution">{icon('warning')}<span>A record of home remedies from 1985, with the book's amounts and doses reworded. It is not medical advice.</span></p>
  <ul class="remedies">{remedies}</ul>
  {lad_note}
  <p class="fine">Summarised from Herminia de Guzman-Ladion, <i>{LADION}</i> (Manila: Philippine Publishing House, 1985), where this plant is shown as “{esc(lad['title'])}” on page {lad['page']}. The book is in copyright, so its wording and photographs are not reproduced. Amounts are the book's, restated.</p>
</section>'''
    # research
    pa = p['papers']
    if pa['items']:
        more = ''
        if pa.get('query'):
            more = (f'<a class="more" href="https://europepmc.org/search?query={urllib.parse.quote(pa["query"])}" target="_blank" '
                    f'rel="noopener">All {pa["total"]} results on Europe PMC {icon("external")}</a>')
        where = 'in the title' if pa.get('scope') == 'title' else 'in the abstract'
        research = f'''<section class="research" aria-labelledby="rs-h">
  <h2 id="rs-h">{icon('flask')} Recent research</h2>
  <p class="fine">The most cited papers since {pa['since']} that name this plant {where}, pulled from Europe PMC in {FETCHED}. Titles are the authors' own and the findings have not been reviewed here.</p>
  <ol class="papers">{''.join(paper_html(it) for it in pa['items'])}</ol>
  {more}
</section>'''
    else:
        why = ('This entry has no settled modern name to search for.' if not p['accepted']
               else f'Europe PMC lists no papers since 2018 that name <i>{esc(p["sci"])}</i>.')
        research = f'''<section class="research" aria-labelledby="rs-h">
  <h2 id="rs-h">{icon('flask')} Recent research</h2>
  <p>{why}</p>
</section>'''
    pager = f'''<nav class="pager wrap" aria-label="Neighbouring entries">
  {f'<a class="prev" href="{prev["slug"]}.html">{icon("left")}<span><small>Previous</small>{esc(prev["title"])}</span></a>' if prev else '<span></span>'}
  {f'<a class="next" href="{nxt["slug"]}.html"><span><small>Next</small>{esc(nxt["title"])}</span>{icon("right")}</a>' if nxt else '<span></span>'}
</nav>'''
    body = f'''{head}
<div class="wrap plant-top">
  {figure}
  <div class="plant-facts">{facts}{note}</div>
</div>
<div class="wrap plant-body">
  <div class="plant-main">
  {today_html(p)}
  {text}
  </div>
  {research}
</div>
{pager}'''
    where = ' and '.join(x for x, on in (('The Medicinal Plants of the Philippines, 1901', p['tavera']), (f'{LADION}, 1985', lad)) if on)
    desc = f'{p["title"]} ({p["sci"]}) in {where}: names, uses, colours, native range, photo and recent research.'
    (DOCS / 'plants' / f'{p["slug"]}.html').write_text(
        page(f'{p["title"]} · Halamang Gamot Directory', desc, body, depth=1, active='plants'), encoding='utf-8')


def build_families(plants):
    groups = {}
    for p in plants:
        if not p['tavera']:
            continue
        groups.setdefault(p['group'], {}).setdefault(p['family'], []).append(p)
    out = []
    for g, fams in groups.items():
        blocks = []
        for fam, ps in fams.items():
            english = next((p['family_en'] for p in ps if p.get('family_en')), '')
            items = ''.join(
                f'<li><a href="plants/{p["slug"]}.html">{esc(p["title"])}</a> <i>{esc(p["sci"])}</i></li>' for p in ps)
            blocks.append(f'<section class="family"><h3>{esc(fam)}</h3>'
                          f'{f"<p class=fine>{esc(english)}</p>" if english else ""}<ul>{items}</ul></section>')
        out.append(f'<section class="fam-group"><h2>{esc(g)}</h2><div class="fam-cols">{"".join(blocks)}</div></section>')
    n_fam = sum(len(f) for f in groups.values())
    body = f'''<header class="page-head wrap">
  <h1>Families</h1>
  <p class="lede">The 1901 book arranges its plants by botanical family, and this page follows it. The 1985 book runs in alphabetical order, so plants found only there are not listed here. The {n_fam} family names below are the ones it prints, so Leguminosae and Compositae appear where a modern flora says Fabaceae and Asteraceae.</p>
</header>
<div class="wrap families">{''.join(out)}</div>'''
    (DOCS / 'families.html').write_text(page(
        'Families · Halamang Gamot Directory', 'Every plant in the directory, grouped by the botanical families the 1901 book uses.',
        body, active='families'), encoding='utf-8')


def build_about(plants):
    langs = ''.join(f'<div><dt>{a}</dt><dd>{b}</dd></div>' for a, b in LANGS)
    specimens = sum(1 for p in plants if p['photo'] and p['photo'].get('specimen'))
    with_tl = sum(1 for p in plants if p['about_tl'])
    with_powo = sum(1 for p in plants if p['about_powo'])
    no_ph = sum(1 for p in plants if not (p['ph'] or {}).get('total'))
    renamed = sum(1 for p in plants if p['tavera'] and p['accepted'] and fold(p['printed']) != fold(p['sci']))
    n_tavera = sum(1 for p in plants if p['tavera'])
    n_ladion = sum(1 for p in plants if p['ladion'])
    n_both = sum(1 for p in plants if p['tavera'] and p['ladion'])
    groups = ', '.join(label.lower() for _, label, _, _ in AILMENTS)
    body = f'''<header class="page-head wrap">
  <h1>About the books</h1>
  <p class="lede">Trinidad H. Pardo de Tavera published <i>Plantas medicinales de Filipinas</i> in Madrid in 1892. Jerome B. Thomas Jr., a captain and assistant surgeon with the United States Volunteers, translated and revised it as <i>The Medicinal Plants of the Philippines</i>, printed in Philadelphia by P. Blakiston's Son &amp; Co. in 1901.</p>
</header>
<div class="wrap about prose">
  <section>
    <h2>What Pardo de Tavera set down</h2>
    <p>Pardo de Tavera was a Filipino physician trained in Paris. For each plant he gives the names used in Tagalog, Visayan, Ilocano, Pampango and Spanish, how healers and doctors used it, a dose where he had one, a botanical description, and where it grew. Thomas added English names, plant sizes and flower colours for army medical officers posted to small stations across the islands.</p>
    <p>The book covers {n_tavera} plants. Read the full text on <a href="{GUTENBERG}" target="_blank" rel="noopener">Project Gutenberg</a> or page through the scan at the <a href="{ARCHIVE}" target="_blank" rel="noopener">Internet Archive</a>.</p>
  </section>
  <section>
    <h2>The second book: <i>{LADION}</i></h2>
    <p>Herminia de Guzman-Ladion, a nurse and physical therapist, wrote <i>{LADION}: Guide to the Effective Use of Medicinal Plants</i> for households. Philippine Publishing House in Manila printed it in 1985. It pairs water treatments with plant remedies for some forty everyday complaints, from abscesses to worms, then shows {n_ladion} plants one to a page with a photograph, the scientific name and the names used in Tagalog, Ilocano, Visayan, Bicol and Pampango.</p>
    <p>{n_both} of those plants are also in the 1901 book, and their pages here carry both accounts. The other {n_ladion - n_both} have pages of their own. Three plants the remedies call for, tagulinaw, malabulak and lumbang bato, have no plant page in the book and are left out.</p>
    <p>The book is still in copyright. Its entries here are a summary written for this site: which ailment each plant is used for, which part, in what form, and the amounts and doses the book gives, with the page number. All of it is reworded. The book's own text and its photographs are not reproduced. Where the scan is too faint to read an amount, the entry says less instead of guessing. Names are given as printed, misprints included, beside the accepted name.</p>
  </section>
  <section>
    <h2>Filtering by ailment</h2>
    <p>The home page can narrow the list to plants used for one group of ailments: {groups}. For the 1985 book the groups follow its chapters, so athlete's foot, eczema and ringworm all fall under skin. The 1901 book has no such chapters, so a script looks through each plant's “Uses” text for the words of that time, such as febrifuge, anthelmintic or emmenagogue. A match means the book mentions the ailment in that entry. It can catch a passing remark, and it can miss a use described in other words, so read the entry itself before relying on a tag.</p>
  </section>
  <section>
    <h2>How this directory was put together</h2>
    <p>The book's text comes from the Project Gutenberg transcription, split into one entry per plant by a script. Nothing in the quoted passages has been reworded. Where the book describes two or three species in a single account, each of their pages carries that account.</p>
    <p>Botanical names have moved a long way since 1901. {renamed} of the {n_tavera} entries carry a different accepted name today, and each page shows both the name as printed and the modern one. Some of the book's identifications were wrong for the Philippine plant, usually because a name from Indian botany was applied to a local species. Those pages carry a note.</p>
    <p>Modern names, colours and native ranges were compiled by hand and checked against the GBIF backbone taxonomy. Photos are the lead image of each species' English Wikipedia article, or the image on its Wikidata record, with the photographer and licence read from Wikimedia Commons. Where Commons has nothing, the page uses an openly licensed photo from <a href="https://www.inaturalist.org/" target="_blank" rel="noopener">iNaturalist</a>. For the {specimens} species with neither, it shows a pressed specimen from the herbarium at the Royal Botanic Gardens, Kew, taken from <a href="https://powo.science.kew.org/" target="_blank" rel="noopener">Plants of the World Online</a>.</p>
    <p>Research links come from Europe PMC, fetched in {FETCHED}. For each plant the script asks for papers since 2022 with the species name in the title, pooling older synonyms still used in journals, and keeps the three with the most citations. If none exist it widens the search to 2018, then to abstracts. The list shows what researchers are studying. It does not vouch for any result.</p>
  </section>
  <section>
    <h2>Modern descriptions and Philippine records</h2>
    <p>Each page carries a short modern description. It is the first few sentences of the plant's English Wikipedia article and, for the {with_tl} plants that have one, of its Tagalog Wikipedia article, quoted under the Creative Commons Attribution-ShareAlike 4.0 licence and linked to the full article. {with_powo} species have no English article, so their pages quote the summary line from Kew's Plants of the World Online.</p>
    <p>The list of provinces comes from <a href="https://www.gbif.org/" target="_blank" rel="noopener">GBIF</a>, which pools herbarium specimens and field observations. The script counts each plant's Philippine records by province. The counts follow where people have collected and photographed plants, so a common garden herb can show fewer records than a rare forest tree, and {no_ph} plants in the book have no Philippine records at all.</p>
  </section>
  <section>
    <h2>Reading the old spellings</h2>
    <p>Pardo de Tavera used his own orthography for Philippine languages. His <i>g̃</i> is the sound now written <i>ng</i>, so <i>Malug̃ay</i> is malunggay and <i>Bawag̃</i> is bawang. He writes <i>k</i> and <i>w</i> where Spanish spelling of the time used <i>c</i>, <i>qu</i> and <i>u</i>.</p>
    <dl class="langs">{langs}</dl>
    <p>Sizes in the botanical descriptions use the marks ° and ′, which read as feet and inches. The book does not explain them.</p>
  </section>
  <section>
    <h2>Plants the book could not name</h2>
    <p>For ten plants Pardo de Tavera wrote a question mark or "not known" where the Philippine name should be. Those pages add names from two later references: <a href="https://stuartxchange.com/" target="_blank" rel="noopener">StuartXchange</a>, Dr. Godofredo Stuart's compilation of Philippine medicinal plants, and <a href="https://plantuse.plantnet.org/en/Category:PROSEA" target="_blank" rel="noopener">PROSEA</a>, the Plant Resources of South-East Asia handbooks. Five of the ten have names there. For the other five, PROSEA lists names from neighbouring countries but none from the Philippines.</p>
  </section>
  <section>
    <h2>A caution</h2>
    <p>The remedies belong to the medicine of the 1890s and the home practice of the 1980s. The 1901 book recommends plants now known to be dangerous, among them St. Ignatius bean, croton, yellow oleander and rosary pea, and its doses were written for physicians of that time. The 1985 book has dried talumpunay and kalatsutsi leaves smoked for asthma and puts oleander on the skin, all of which carry real risk. Treat both texts as history.</p>
  </section>
  <section>
    <h2>Corrections</h2>
    <p>The data and build scripts are in the <a href="{REPO}" target="_blank" rel="noopener">GitHub repository</a>. If a name, colour, photo or range is wrong, <a href="{REPO}/issues" target="_blank" rel="noopener">open an issue</a>.</p>
  </section>
</div>'''
    (DOCS / 'about.html').write_text(page(
        'About the books · Halamang Gamot Directory',
        f"About Pardo de Tavera's The Medicinal Plants of the Philippines, de Guzman-Ladion's {LADION}, and how this directory was built.",
        body, active='about'), encoding='utf-8')


def build_404():
    body = '''<header class="page-head wrap">
  <h1>Page not found</h1>
  <p class="lede">That address does not match a plant or page in the directory.</p>
  <p><a class="button" href="/halamang-gamot-directory/">Back to all plants</a></p>
</header>'''
    out = page('Page not found · Halamang Gamot Directory', 'Page not found.', body)
    out = out.replace('src="assets/', 'src="/halamang-gamot-directory/assets/')
    out = out.replace('href="assets/', 'href="/halamang-gamot-directory/assets/').replace(
        'href="index.html"', 'href="/halamang-gamot-directory/"').replace(
        'href="families.html"', 'href="/halamang-gamot-directory/families.html"').replace(
        'href="about.html"', 'href="/halamang-gamot-directory/about.html"')
    (DOCS / '404.html').write_text(out, encoding='utf-8')


def main():
    plants = load()
    (DOCS / 'plants').mkdir(parents=True, exist_ok=True)
    for old in (DOCS / 'plants').glob('*.html'):
        old.unlink()
    build_index(plants)
    for i, p in enumerate(plants):
        build_plant(p, plants[i - 1] if i else None, plants[i + 1] if i + 1 < len(plants) else None)
    build_families(plants)
    build_about(plants)
    build_404()
    (DOCS / '.nojekyll').write_text('', encoding='utf-8')
    (DOCS / 'assets' / 'favicon.svg').write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><rect width="256" height="256" rx="56" fill="#1f5a3d"/>'
        f'<g transform="translate(40 40) scale(.6875)"><path fill="#eaf3e4" d="{ICON_PATHS["leaf"]}"/></g></svg>', encoding='utf-8')
    print(f'built {len(plants)} plant pages')


main()
