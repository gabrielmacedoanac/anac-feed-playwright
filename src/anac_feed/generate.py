import email.utils
import html
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from .config import DATA, ROOT, SITE

TITLE = "Anac Feed"
DESCRIPTION = (
    "Feed com noticias, videos e legislacoes publicados pela "
    "Agencia Nacional de Aviacao Civil (Anac)."
)
AGENCY = "Agência Nacional de Aviação Civil (Anac)"
AGENCY_URL = "https://www.gov.br/anac/pt-br"


def esc(value):
    return html.escape(str(value or ""), quote=True)


def parsed(item):
    value = item.get("iso")
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def write_json(items):
    DATA.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": TITLE,
        "home_page_url": SITE,
        "feed_url": SITE + "data/feed.json",
        "description": DESCRIPTION,
        "language": "pt-BR",
        "authors": [{"name": AGENCY, "url": AGENCY_URL}],
        "generated": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "items": items,
    }
    (DATA / "feed.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_rss(items):
    atom_ns = "http://www.w3.org/2005/Atom"
    media_ns = "http://search.yahoo.com/mrss/"
    ET.register_namespace("atom", atom_ns)
    ET.register_namespace("media", media_ns)

    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")

    channel_values = (
        ("title", TITLE),
        ("link", SITE),
        ("description", DESCRIPTION),
        ("language", "pt-BR"),
        (
            "lastBuildDate",
            email.utils.format_datetime(
                datetime.now(timezone.utc),
                usegmt=True,
            ),
        ),
        ("generator", "ANAC Feed Python Generator"),
    )
    for tag, value in channel_values:
        ET.SubElement(channel, tag).text = value

    ET.SubElement(
        channel,
        f"{{{atom_ns}}}link",
        {
            "href": SITE + "data/rss.xml",
            "rel": "self",
            "type": "application/rss+xml",
        },
    )

    for content_item in items:
        node = ET.SubElement(channel, "item")
        values = (
            ("title", content_item.get("title")),
            ("link", content_item.get("link")),
            ("guid", content_item.get("link")),
            ("description", content_item.get("description")),
            ("category", content_item.get("type")),
        )
        for tag, value in values:
            ET.SubElement(node, tag).text = value or ""

        date_value = parsed(content_item)
        if date_value:
            ET.SubElement(node, "pubDate").text = email.utils.format_datetime(
                date_value.astimezone(timezone.utc),
                usegmt=True,
            )

        if content_item.get("image"):
            ET.SubElement(
                node,
                f"{{{media_ns}}}thumbnail",
                {"url": content_item["image"]},
            )

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(DATA / "rss.xml", encoding="utf-8", xml_declaration=True)


def write_atom(items):
    namespace = "http://www.w3.org/2005/Atom"
    ET.register_namespace("", namespace)
    root = ET.Element(f"{{{namespace}}}feed")

    feed_values = (
        ("title", TITLE),
        ("subtitle", DESCRIPTION),
        ("id", SITE),
        ("updated", datetime.now(timezone.utc).isoformat()),
    )
    for tag, value in feed_values:
        ET.SubElement(root, f"{{{namespace}}}{tag}").text = value

    ET.SubElement(
        root,
        f"{{{namespace}}}link",
        {"href": SITE, "rel": "alternate", "type": "text/html"},
    )
    ET.SubElement(
        root,
        f"{{{namespace}}}link",
        {
            "href": SITE + "data/atom.xml",
            "rel": "self",
            "type": "application/atom+xml",
        },
    )

    author = ET.SubElement(root, f"{{{namespace}}}author")
    ET.SubElement(author, f"{{{namespace}}}name").text = AGENCY
    ET.SubElement(author, f"{{{namespace}}}uri").text = AGENCY_URL

    for content_item in items:
        entry = ET.SubElement(root, f"{{{namespace}}}entry")
        ET.SubElement(entry, f"{{{namespace}}}title").text = content_item.get(
            "title", ""
        )
        ET.SubElement(entry, f"{{{namespace}}}id").text = content_item.get(
            "link", ""
        )
        ET.SubElement(
            entry,
            f"{{{namespace}}}link",
            {
                "href": content_item.get("link", ""),
                "rel": "alternate",
                "type": "text/html",
            },
        )

        published = content_item.get("iso") or datetime.now(
            timezone.utc
        ).isoformat()
        ET.SubElement(entry, f"{{{namespace}}}published").text = published
        ET.SubElement(entry, f"{{{namespace}}}updated").text = published
        ET.SubElement(
            entry,
            f"{{{namespace}}}category",
            {"term": content_item.get("type", "")},
        )
        ET.SubElement(
            entry,
            f"{{{namespace}}}summary",
            {"type": "text"},
        ).text = content_item.get("description", "")

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(DATA / "atom.xml", encoding="utf-8", xml_declaration=True)


def filter_navigation():
    return """
    <div class="filter-buttons">
      <button type="button" data-type="all" onclick="filterByType('all')" class="active">
        <i class="fas fa-list" aria-hidden="true"></i>Todos
      </button>
      <button type="button" data-type="notícia" onclick="filterByType('notícia')">
        <i class="fas fa-newspaper" aria-hidden="true"></i>Notícias
      </button>
      <button type="button" data-type="vídeo" onclick="filterByType('vídeo')">
        <i class="fas fa-video" aria-hidden="true"></i>Vídeos
      </button>
      <button type="button" data-type="legislação" onclick="filterByType('legislação')">
        <i class="fas fa-gavel" aria-hidden="true"></i>Legislações
      </button>
    </div>
    """


def filter_script():
    return """
    <script>
      function filterByType(type) {
        const articles = document.querySelectorAll('.feed-container article');
        const buttons = document.querySelectorAll('.filter-buttons button');

        articles.forEach((article) => {
          const articleType = article.getAttribute('data-type') || '';
          article.style.display =
            type === 'all' || articleType === type ? 'block' : 'none';
        });

        buttons.forEach((button) => {
          const buttonType = button.getAttribute('data-type') || '';
          button.classList.toggle('active', buttonType === type);
        });
      }

      document.addEventListener('DOMContentLoaded', () => {
        filterByType('all');
      });
    </script>
    """


def write_simple_html(items):
    feed_items = []

    for content_item in items:
        feed_items.append(
            f"""
    <div class="feed-item" data-type="{esc(content_item.get('type'))}">
      <a
        href="{esc(content_item.get('link'))}"
        target="_blank"
        rel="noopener noreferrer"
        class="feed-item-title"
      >{esc(content_item.get('title'))}</a>
      <span class="feed-item-meta">
        ({esc(content_item.get('display'))} - {esc(content_item.get('type'))})
      </span>
      <div class="feed-item-description">
        {esc(content_item.get('description'))}
      </div>
    </div>
            """
        )

    document = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(TITLE)}</title>
  <meta name="description" content="{esc(DESCRIPTION)}">
  <link rel="canonical" href="{esc(SITE)}data/">
  <link rel="alternate" href="rss.xml" type="application/rss+xml" title="RSS">
  <link rel="alternate" href="atom.xml" type="application/atom+xml" title="Atom">
  <link rel="alternate" href="feed.json" type="application/feed+json" title="JSON Feed">
  <style>
    .filters {{ text-align: center; margin-bottom: 1rem; }}
    .filters a {{ margin: 0 .5rem; color: blue; text-decoration: none; }}
    .filters a:hover, .filters a.active {{ text-decoration: underline; }}
    .filters a.active {{ font-weight: bold; }}
    .feed-item {{ margin-bottom: 1rem; }}
    .feed-item[hidden] {{ display: none; }}
    .feed-item-description {{ margin-top: .5rem; color: #222; font-size: .9rem; }}
    .feed-item-title {{ font-size: 1rem; }}
    .feed-item-meta {{ color: #555; font-size: .8rem; vertical-align: text-top; }}
    footer {{ margin-top: 1rem; color: #333; font-size: .8rem; text-align: center; }}
    footer a {{ margin: 0 .5rem; color: blue; text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="filters">
    <a href="#" data-filter="all" class="active" onclick="filterSimpleByType('all'); return false;">[Todos]</a>
    <a href="#" data-filter="notícia" onclick="filterSimpleByType('notícia'); return false;">[Notícias]</a>
    <a href="#" data-filter="vídeo" onclick="filterSimpleByType('vídeo'); return false;">[Vídeos]</a>
    <a href="#" data-filter="legislação" onclick="filterSimpleByType('legislação'); return false;">[Legislações]</a>
  </div>

  <div id="content">{''.join(feed_items)}</div>

  <footer>
    <p><a href="../index.html">Versão semântica</a></p>
    <div>
      <a href="rss.xml" target="_blank" rel="noopener noreferrer">RSS Feed</a>
      <a href="feed.json" target="_blank" rel="noopener noreferrer">JSON Feed</a>
      <a href="atom.xml" target="_blank" rel="noopener noreferrer">ATOM Feed</a>
      <a href="anac_feed.json" target="_blank" rel="noopener noreferrer">JSON consolidado</a>
    </div>
  </footer>

  <script>
    function filterSimpleByType(type) {{
      const items = document.querySelectorAll('.feed-item');
      const controls = document.querySelectorAll('.filters [data-filter]');

      items.forEach((item) => {{
        const itemType = item.getAttribute('data-type') || '';
        item.hidden = type !== 'all' && itemType !== type;
      }});

      controls.forEach((control) => {{
        control.classList.toggle(
          'active',
          control.getAttribute('data-filter') === type
        );
      }});
    }}

    document.addEventListener('DOMContentLoaded', () => {{
      filterSimpleByType('all');
    }});
  </script>
</body>
</html>
"""

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "index.html").write_text(document, encoding="utf-8")


def write_semantic_html(items):
    cards = []
    type_classes = {
        "notícia": "type-notícia",
        "vídeo": "type-vídeo",
        "legislação": "type-legislação",
    }
    schema_types = {
        "notícia": "NewsArticle",
        "vídeo": "VideoObject",
        "legislação": "Legislation",
    }

    for content_item in items:
        item_type = content_item.get("type") or "notícia"
        type_class = type_classes.get(item_type, "type-notícia")
        schema_type = schema_types.get(item_type, "CreativeWork")
        image = ""

        if content_item.get("image"):
            image = (
                '<img class="article-image" property="image" '
                f'src="{esc(content_item.get("image"))}" '
                f'alt="{esc(content_item.get("title"))}" loading="lazy">'
            )

        cards.append(
            f"""
    <article data-type="{esc(item_type)}" typeof="{schema_type}">
      {image}
      <div class="article-content">
        <div class="article-meta">
          <time property="datePublished" datetime="{esc(content_item.get('iso'))}">
            {esc(content_item.get('display'))}
          </time>
          <span
            class="article-type {type_class}"
            role="button"
            tabindex="0"
            onclick="filterByType('{esc(item_type)}')"
            onkeydown="if (event.key === 'Enter' || event.key === ' ') {{ event.preventDefault(); filterByType('{esc(item_type)}'); }}"
          >{esc(item_type)}</span>
        </div>
        <h2 property="headline">
          <a href="{esc(content_item.get('link'))}" target="_blank" rel="noopener noreferrer">
            {esc(content_item.get('title'))}
          </a>
        </h2>
        <p class="article-description" property="description">
          {esc(content_item.get('description'))}
        </p>
      </div>
    </article>
            """
        )

    document = f"""<!DOCTYPE html>
<html lang="pt-BR" vocab="https://schema.org/">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(TITLE)}</title>
  <meta name="description" content="{esc(DESCRIPTION)}">
  <link rel="canonical" href="{esc(SITE)}">
  <link rel="alternate" href="data/rss.xml" type="application/rss+xml" title="RSS">
  <link rel="alternate" href="data/atom.xml" type="application/atom+xml" title="Atom">
  <link rel="alternate" href="data/feed.json" type="application/feed+json" title="JSON Feed">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
  <style>
    :root {{
      --primary: #0066cc;
      --secondary: #004080;
      --light: #f8f9fa;
      --dark: #212529;
      --success: #28a745;
      --danger: #dc3545;
      --border-radius: .25rem;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ margin: 0; color: var(--dark); background: #f5f5f5; font-family: "Segoe UI", system-ui, sans-serif; line-height: 1.6; }}
    header {{ width: 100%; margin-bottom: 2rem; padding: 2rem 1rem; color: white; text-align: center; background: linear-gradient(135deg, var(--primary), var(--secondary)); box-shadow: 0 2px 5px #0002; }}
    h1 {{ margin-bottom: .5rem; font-size: 2.2rem; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 0 1rem; }}
    .simple-link {{ margin-top: .75rem; }}
    .simple-link a {{ color: white; font-weight: 600; }}
    .filter-buttons {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 1rem; margin-bottom: 2rem; }}
    .filter-buttons button {{ display: flex; align-items: center; justify-content: center; padding: .5rem 1rem; color: white; background: var(--primary); border: 0; border-radius: var(--border-radius); font-size: 1rem; cursor: pointer; }}
    .filter-buttons button i {{ margin-right: .5rem; }}
    .filter-buttons button:hover {{ background: var(--secondary); }}
    .filter-buttons button.active {{ background: var(--success); }}
    .filter-buttons button:focus-visible, .article-type:focus-visible {{ outline: 3px solid #ffbf47; outline-offset: 3px; }}
    .feed-container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; justify-content: center; padding: 1rem; }}
    article {{ overflow: hidden; background: white; border-radius: var(--border-radius); box-shadow: 0 2px 10px #0002; transition: transform .2s, box-shadow .2s; }}
    article:hover {{ transform: translateY(-5px); box-shadow: 0 5px 15px #0002; }}
    article[hidden] {{ display: none !important; }}
    .article-image {{ width: 100%; height: 200px; object-fit: cover; }}
    .article-content {{ padding: 1.5rem; }}
    .article-meta {{ display: flex; align-items: center; justify-content: space-between; gap: .75rem; margin-bottom: 1rem; color: #6c757d; font-size: .9rem; }}
    .article-type {{ display: inline-block; padding: .25rem .5rem; border-radius: var(--border-radius); font-size: .8rem; font-weight: bold; text-transform: uppercase; cursor: pointer; }}
    .type-notícia {{ color: var(--primary); background: rgb(236, 248, 254); }}
    .type-vídeo {{ color: var(--danger); background: #fff0f0; }}
    .type-legislação {{ color: var(--success); background: #f0fff4; }}
    h2 {{ margin-bottom: 1rem; font-size: 1.4rem; }}
    h2 a {{ color: var(--dark); text-decoration: none; }}
    h2 a:hover {{ color: var(--primary); text-decoration: underline; }}
    .article-description {{ margin-bottom: 1rem; color: #495057; overflow-wrap: break-word; }}
    footer {{ margin-top: 2rem; padding: 1.5rem; color: white; text-align: center; background: var(--dark); }}
    .feed-links {{ margin-top: 1rem; text-align: center; }}
    .feed-links a {{ margin: 0 .5rem; color: #8ec5ff; text-decoration: none; }}
    .feed-links a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <header typeof="WPHeader">
    <div class="container">
      <h1 property="name">{esc(TITLE)}</h1>
      <p property="description">{esc(DESCRIPTION)}</p>
      <p class="simple-link"><a href="data/index.html">Versão HTML simples</a></p>
    </div>
  </header>

  <main class="container">
    {filter_navigation()}
    <section class="feed-container" aria-label="Publicações">
      {''.join(cards)}
    </section>
  </main>

  <footer typeof="WPFooter">
    <div class="container">
      <div class="feed-links">
        <a href="data/index.html">HTML simples</a>
        <a href="data/rss.xml">RSS Feed</a>
        <a href="data/feed.json">JSON Feed</a>
        <a href="data/atom.xml">ATOM Feed</a>
        <a href="data/anac_feed.json">JSON consolidado</a>
      </div>
    </div>
  </footer>

  {filter_script()}
</body>
</html>
"""

    (ROOT / "index.html").write_text(document, encoding="utf-8")


def generate(items):
    write_json(items)
    write_rss(items)
    write_atom(items)
    write_simple_html(items)
    write_semantic_html(items)
