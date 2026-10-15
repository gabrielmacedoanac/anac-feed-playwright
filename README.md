# ANAC Feed Playwright

Pipeline otimizado para GitHub Actions. Usa uma única instância do Chromium para notícias e legislação, e o feed Atom público do YouTube para vídeos.

## Executar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m playwright install --with-deps chromium
python -m anac_feed
```

## Saídas

- `index.html`
- `data/index.html`
- `data/feed.json`
- `data/rss.xml`
- `data/atom.xml`
- `data/anac_feed.json`


## Repositório

- GitHub: `gabrielmacedoanac/anac-feed-playwright`
- GitHub Pages: `https://gabrielmacedoanac.github.io/anac-feed-playwright/`
