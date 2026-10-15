from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'; DEBUG=ROOT/'anac_feed_debug'
NEWS='https://www.gov.br/anac/pt-br/noticias'
LEGISLATION='https://www.anac.gov.br/assuntos/legislacao/ultimos-atos-publicados'
CHANNEL_ID='UC5ynmbMZXolM-jo2hGR31qg'
YOUTUBE=f'https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}'
SITE='https://gabrielmacedoanac.github.io/anac-feed-playwright/'
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36'
MAX_NEWS=20; MAX_VIDEOS=15; MAX_LAWS=20; TIMEOUT=120_000
