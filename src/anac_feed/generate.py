import email.utils, html, json, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from .config import ROOT, DATA, SITE
TITLE='Anac Feed';DESCRIPTION='Feed com notícias, vídeos e legislações publicados pela Agência Nacional de Aviação Civil (Anac).';AGENCY='Agência Nacional de Aviação Civil (Anac)';AGENCY_URL='https://www.gov.br/anac/pt-br'
def esc(v):return html.escape(str(v or ''),quote=True)
def parsed(x):
    try:return datetime.fromisoformat((x.get('iso') or '').replace('Z','+00:00'))
    except ValueError:return None
def write_json(items):
    DATA.mkdir(parents=True,exist_ok=True);payload={'version':'https://jsonfeed.org/version/1.1','title':TITLE,'home_page_url':SITE,'feed_url':SITE+'data/feed.json','description':DESCRIPTION,'language':'pt-BR','authors':[{'name':AGENCY,'url':AGENCY_URL}],'generated':datetime.now(timezone.utc).isoformat(),'count':len(items),'items':items};(DATA/'feed.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
def write_rss(items):
    a='http://www.w3.org/2005/Atom';m='http://search.yahoo.com/mrss/';ET.register_namespace('atom',a);ET.register_namespace('media',m);root=ET.Element('rss',{'version':'2.0'});ch=ET.SubElement(root,'channel')
    for t,v in [('title',TITLE),('link',SITE),('description',DESCRIPTION),('language','pt-BR'),('lastBuildDate',email.utils.format_datetime(datetime.now(timezone.utc),usegmt=True)),('generator','ANAC Feed Python Generator')]:ET.SubElement(ch,t).text=v
    ET.SubElement(ch,f'{{{a}}}link',{'href':SITE+'data/rss.xml','rel':'self','type':'application/rss+xml'})
    for x in items:
        n=ET.SubElement(ch,'item')
        for t,v in [('title',x.get('title')),('link',x.get('link')),('guid',x.get('link')),('description',x.get('description')),('category',x.get('type'))]:ET.SubElement(n,t).text=v or ''
        d=parsed(x)
        if d:ET.SubElement(n,'pubDate').text=email.utils.format_datetime(d.astimezone(timezone.utc),usegmt=True)
        if x.get('image'):ET.SubElement(n,f'{{{m}}}thumbnail',{'url':x['image']})
    tree=ET.ElementTree(root);ET.indent(tree,space='  ');tree.write(DATA/'rss.xml',encoding='utf-8',xml_declaration=True)
def write_atom(items):
    n='http://www.w3.org/2005/Atom';ET.register_namespace('',n);root=ET.Element(f'{{{n}}}feed')
    for t,v in [('title',TITLE),('subtitle',DESCRIPTION),('id',SITE),('updated',datetime.now(timezone.utc).isoformat())]:ET.SubElement(root,f'{{{n}}}{t}').text=v
    ET.SubElement(root,f'{{{n}}}link',{'href':SITE,'rel':'alternate','type':'text/html'});ET.SubElement(root,f'{{{n}}}link',{'href':SITE+'data/atom.xml','rel':'self','type':'application/atom+xml'});au=ET.SubElement(root,f'{{{n}}}author');ET.SubElement(au,f'{{{n}}}name').text=AGENCY;ET.SubElement(au,f'{{{n}}}uri').text=AGENCY_URL
    for x in items:
        e=ET.SubElement(root,f'{{{n}}}entry');ET.SubElement(e,f'{{{n}}}title').text=x.get('title','');ET.SubElement(e,f'{{{n}}}id').text=x.get('link','');ET.SubElement(e,f'{{{n}}}link',{'href':x.get('link',''),'rel':'alternate','type':'text/html'});p=x.get('iso') or datetime.now(timezone.utc).isoformat();ET.SubElement(e,f'{{{n}}}published').text=p;ET.SubElement(e,f'{{{n}}}updated').text=p;ET.SubElement(e,f'{{{n}}}category',{'term':x.get('type','')});ET.SubElement(e,f'{{{n}}}summary',{'type':'text'}).text=x.get('description','')
    tree=ET.ElementTree(root);ET.indent(tree,space='  ');tree.write(DATA/'atom.xml',encoding='utf-8',xml_declaration=True)
def write_html(items):
    simple=[];cards=[]
    for x in items:
        simple.append(f'<div class="feed-item" data-type="{esc(x.get("type"))}"><a href="{esc(x.get("link"))}" target="_blank" rel="noopener noreferrer">{esc(x.get("title"))}</a> <small>({esc(x.get("display"))} - {esc(x.get("type"))})</small><p>{esc(x.get("description"))}</p></div>')
        image=f'<img src="{esc(x.get("image"))}" alt="{esc(x.get("title"))}" loading="lazy">' if x.get('image') else ''
        cards.append(f'<article data-type="{esc(x.get("type"))}">{image}<div><time>{esc(x.get("display"))}</time><span>{esc(x.get("type"))}</span><h2><a href="{esc(x.get("link"))}" target="_blank" rel="noopener noreferrer">{esc(x.get("title"))}</a></h2><p>{esc(x.get("description"))}</p></div></article>')
    script="function f(t){document.querySelectorAll('[data-type]').forEach(i=>i.style.display=t==='all'||i.dataset.type===t?'block':'none')}"
    nav="<nav><button onclick=\"f(\'all\')\">Todos</button><button onclick=\"f(\'notícia\')\">Notícias</button><button onclick=\"f(\'vídeo\')\">Vídeos</button><button onclick=\"f(\'legislação\')\">Legislações</button></nav>"
    DATA.mkdir(parents=True,exist_ok=True);(DATA/'index.html').write_text(f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{TITLE}</title><style>body{{font-family:system-ui;max-width:1100px;margin:auto;padding:1rem}}nav{{text-align:center}}button{{margin:.4rem}}.feed-item{{margin:1rem 0}}</style></head><body>{nav}{"".join(simple)}<footer><a href="rss.xml">RSS</a> <a href="feed.json">JSON</a> <a href="atom.xml">Atom</a></footer><script>{script}</script></body></html>',encoding='utf-8')
    css='body{margin:0;font-family:system-ui;background:#f5f5f5;color:#212529}header{background:linear-gradient(135deg,#06c,#004080);color:white;text-align:center;padding:2rem}.container{max-width:1200px;margin:auto;padding:1rem}nav{text-align:center}button{margin:.4rem;padding:.6rem 1rem}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.5rem}article{background:white;box-shadow:0 2px 10px #0002}article>img{width:100%;height:200px;object-fit:cover}article>div{padding:1.5rem}article span{float:right}footer{text-align:center;padding:2rem;background:#212529}footer a{color:#9cf;margin:1rem}'
    (ROOT/'index.html').write_text(f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{TITLE}</title><meta name="description" content="{esc(DESCRIPTION)}"><style>{css}</style></head><body><header><h1>{TITLE}</h1><p>{DESCRIPTION}</p></header><main class="container">{nav}<div class="grid">{"".join(cards)}</div></main><footer><a href="data/rss.xml">RSS</a><a href="data/feed.json">JSON</a><a href="data/atom.xml">Atom</a></footer><script>{script}</script></body></html>',encoding='utf-8')
def generate(items):write_json(items);write_rss(items);write_atom(items);write_html(items)
