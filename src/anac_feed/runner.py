import asyncio,json,time
from datetime import datetime,timezone
from playwright.async_api import async_playwright
from .config import DATA
from .main import context,news,videos,laws,plone,consolidate
from .generate import generate
from .validate import validate
async def main():
    start=time.perf_counter();result={'noticias':[],'videos':[],'legislacoes':[],'legislacoesPlone':[]};errors={}
    try:result['videos']=videos()
    except Exception as e:errors['videos']=str(e)
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage']);c=await context(browser)
        for name,fn in [('noticias',news),('legislacoes',laws),('legislacoesPlone',plone)]:
            try:result[name]=await fn(c)
            except Exception as e:errors[name]=str(e)
        await c.close();await browser.close()
    items=consolidate(list(result.values()));DATA.mkdir(parents=True,exist_ok=True);payload={'generated':datetime.now(timezone.utc).isoformat(),'counts':{k:len(v) for k,v in result.items()}|{'total':len(items)},'errors':errors,'items':items,'sources':result};(DATA/'anac_feed.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8');generate(items);paths=validate(len(items));print(f'Gerados {len(items)} itens em {time.perf_counter()-start:.2f}s');[print(p) for p in paths];print(json.dumps(errors,ensure_ascii=False,indent=2) if errors else 'Sem erros')
def run():asyncio.run(main())
if __name__=='__main__':run()
