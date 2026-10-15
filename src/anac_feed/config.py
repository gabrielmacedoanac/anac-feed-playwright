from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'; DEBUG=ROOT/'anac_feed_debug'
NEWS='https://www.gov.br/anac/pt-br/noticias'
LEGISLATION='https://www.anac.gov.br/assuntos/legislacao/ultimos-atos-publicados'
PLONE='https://www.anac.gov.br/assuntos/legislacao/busca-legislacao/@@faceted_query?b_start%5B%5D=0&c6%5B%5D=CT&c6%5B%5D=Decis%C3%A3o&c6%5B%5D=Decreto&c6%5B%5D=Decreto-Lei&c6%5B%5D=IAC&c6%5B%5D=IS&c6%5B%5D=Instru%C3%A7%C3%A3o+Normativa&c6%5B%5D=Lei&c6%5B%5D=Lei+Complementar&c6%5B%5D=Medida+Provis%C3%B3ria&c6%5B%5D=PNAVSEC&c6%5B%5D=PNIAVSEC&c6%5B%5D=PROFAL&c6%5B%5D=PSO+-+BR&c6%5B%5D=PSOE+-+ANAC&c6%5B%5D=Portaria+Conjunta&c6%5B%5D=RBAC&c6%5B%5D=RBAC-E&c6%5B%5D=RBHA&c6%5B%5D=Resolu%C3%A7%C3%A3o&c6%5B%5D=SELO+ANAC&c6%5B%5D=TP&c6%5B%5D=iBR2020'
CHANNEL_ID='UC5ynmbMZXolM-jo2hGR31qg'
YOUTUBE=f'https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}'
SITE='https://gabrielmacedoanac.github.io/anac-feed-playwright/'
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36'
MAX_NEWS=20; MAX_VIDEOS=15; MAX_LAWS=20; TIMEOUT=120_000
