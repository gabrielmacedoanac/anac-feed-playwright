import asyncio, email.utils, html, json, re, time, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from .config import *

TZ=timezone(timedelta(hours=-3))
def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def dt(v):
    v=clean(v)
    if not v:return None
    try:
        x=datetime.fromisoformat(v.replace('Z','+00:00')); return x if x.tzinfo else x.replace(tzinfo=TZ)
    except ValueError: pass
    m=re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})(?:\s+(\d{1,2})[h:](\d{2}))?',v)
    if m:
        d,mo,y,h,mi=m.groups()
        try:return datetime(int(y),int(mo),int(d),int(h or 0),int(mi or 0),tzinfo=TZ)
        except ValueError:return None
    return None
def item(title,link,date=None,description='Sem descrição',image=None,kind='notícia',metadata=None,**extra):
    iso=date.isoformat() if date else None
    out={'title':clean(title) or 'Sem título','link':link or '','date':iso or 'ND','description':clean(description) or 'Sem descrição','image':image or None,'type':kind,'display':date.astimezone(TZ).strftime('%d/%m/%Y %Hh%M') if date else 'ND','iso':iso,'dateObj':iso}
    if metadata is not None:out['metadata']=metadata
    out.update(extra);return out

async def context(browser):
    c=await browser.new_context(user_agent=UA,locale='pt-BR',timezone_id='America/Sao_Paulo',viewport={'width':1440,'height':1000})
    async def route(r):
        if r.request.resource_type in {'font','media'}:await r.abort()
        else:await r.continue_()
    await c.route('**/*',route);return c
async def page(c,url):
    p=await c.new_page();p.set_default_timeout(TIMEOUT);r=await p.goto(url,wait_until='domcontentloaded',timeout=TIMEOUT)
    if r is None or r.status>=400:await p.close();raise RuntimeError(f'HTTP {r.status if r else "sem resposta"}: {url}')
    await p.wait_for_timeout(2500);return p
async def debug(p,name):
    DEBUG.mkdir(parents=True,exist_ok=True);(DEBUG/f'{name}.html').write_text(await p.content(),encoding='utf-8');await p.screenshot(path=str(DEBUG/f'{name}.png'),full_page=True)

async def news(c):
    p=await page(c,NEWS)
    try: await debug(p,'noticias');s=BeautifulSoup(await p.content(),'lxml')
    finally: await p.close()
    up=re.compile(r'^https://www\.gov\.br/anac/pt-br/noticias/\d{4}/[^/?#]+/?$',re.I);dp=re.compile(r'publicado\s+(\d{1,2}/\d{1,2}/\d{4})(?:\s+(\d{1,2}h\d{2}))?',re.I)
    out=[];seen=set()
    for a in s.select('a[href]'):
        link=urljoin(NEWS,a.get('href'));title=clean(a.get_text(' ',strip=True))
        if link in seen or not up.match(link) or len(title)<10:continue
        box=a
        for _ in range(12):
            text=clean(box.get_text(' ',strip=True))
            if dp.search(text) or box.parent is None:break
            box=box.parent
        text=clean(box.get_text(' ',strip=True));m=dp.search(text);raw=(m.group(1)+(' '+m.group(2) if m and m.group(2) else '')) if m else ''
        desc=next((clean(x.get_text(' ',strip=True)) for x in box.select('p') if clean(x.get_text(' ',strip=True)) not in {'',title,'Notícia'} and not re.match(r'^(tags?\s*:|publicado\b)',clean(x.get_text(' ',strip=True)),re.I)),'Sem descrição')
        im=box.select_one('img');image=None
        if im:
            for at in ('src','data-src','data-lazy-src','data-original'):
                if im.get(at) and not im.get(at).startswith('data:'):image=urljoin(NEWS,im.get(at));break
        out.append(item(title,link,dt(raw),desc,image));seen.add(link)
        if len(out)>=MAX_NEWS:break
    return out

def videos():
    ns={'a':'http://www.w3.org/2005/Atom','y':'http://www.youtube.com/xml/schemas/2015','m':'http://search.yahoo.com/mrss/'}
    req=urllib.request.Request(YOUTUBE,headers={'User-Agent':UA,'Accept':'application/atom+xml,application/xml'})
    with urllib.request.urlopen(req,timeout=45) as r:root=ET.fromstring(r.read())
    def txt(n,path,default=''):return clean(n.findtext(path,default=default,namespaces=ns)) if n is not None else default
    channel=txt(root,'a:title','Oficial ANAC');cid=txt(root,'y:channelId',CHANNEL_ID);out=[]
    for e in root.findall('a:entry',ns)[:MAX_VIDEOS]:
        vid=txt(e,'y:videoId')
        if not vid:continue
        title=txt(e,'a:title','Sem título');published=txt(e,'a:published');updated=txt(e,'a:updated');media=e.find('m:group',ns);desc=txt(media,'m:description','Sem descrição');th=media.find('m:thumbnail',ns) if media is not None else None;image=th.get('url') if th is not None else f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg';link=f'https://www.youtube.com/watch?v={vid}'
        out.append(item(title,link,dt(published),desc,image,'vídeo',{'publishedDate':published,'modifiedDate':updated or published},videoId=vid,channel=channel,channelId=cid,thumbnailUrl=image,contentUrl=link,embedUrl=f'https://www.youtube.com/embed/{vid}',uploadDate=published or 'ND'))
    return out

async def laws(c):
    datep=re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b');out=[];seen=set();visited=set();url=LEGISLATION
    while url and url not in visited and len(out)<MAX_LAWS:
        visited.add(url);p=await page(c,url)
        try:await debug(p,f'legislacao_{len(visited)}');core=BeautifulSoup(await p.content(),'lxml').select_one('#content-core')
        finally:await p.close()
        if not core:break
        for tile in core.select('.tileItem'):
            a=tile.select_one('a[href]');d=tile.select_one('.description')
            if not a or not d:continue
            title=clean(a.get_text(' ',strip=True));link=urljoin(url,a.get('href'));desc=clean(d.get_text(' ',strip=True));m=datep.search(clean(tile.get_text(' ',strip=True)))
            if 'portaria-de-pessoal' in link.lower().replace('_','-') or link in seen or not desc:continue
            out.append(item(title,link,dt(m.group(0) if m else ''),desc,None,'legislação'));seen.add(link)
            if len(out)>=MAX_LAWS:break
        nxt=core.select_one('a[rel="next"],a.next,.next a,.pagination-next a,li.next a,a[title*="Próxima" i],a[title*="Seguinte" i]');url=urljoin(url,nxt.get('href')) if nxt and nxt.get('href') else None
    return out

def dated(x):
    try:return datetime.fromisoformat((x.get('iso') or '').replace('Z','+00:00'))
    except ValueError:return datetime.min.replace(tzinfo=timezone.utc)
def consolidate(groups):
    seen={};
    for x in sum(groups,[]):
        if x.get('link'):seen[(x.get('type'),x['link'])]=x
    return sorted(seen.values(),key=dated,reverse=True)
