import json, xml.etree.ElementTree as ET
from html.parser import HTMLParser
from .config import ROOT,DATA
class V(HTMLParser):
    def __init__(self):super().__init__();self.errors=[];self.articles=0
    def handle_starttag(self,t,a):
        d=dict(a)
        if t=='a' and not d.get('href'):self.errors.append('link sem href')
        if t=='img' and (not d.get('src') or 'alt' not in d):self.errors.append('imagem inválida')
        if t=='article':self.articles+=1
def validate(expected):
    paths=[ROOT/'index.html',DATA/'index.html',DATA/'feed.json',DATA/'rss.xml',DATA/'atom.xml',DATA/'anac_feed.json']
    for p in paths:
        if not p.exists() or p.stat().st_size==0:raise RuntimeError(f'Arquivo inválido: {p}')
    for p in paths[:2]:
        v=V();v.feed(p.read_text(encoding='utf-8'))
        if v.errors:raise RuntimeError(f'{p}: {v.errors}')
    if json.loads((DATA/'feed.json').read_text(encoding='utf-8')).get('count')!=expected:raise RuntimeError('Contagem JSON divergente')
    ET.parse(DATA/'rss.xml');ET.parse(DATA/'atom.xml');return paths
