import email.utils
import html
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from .config import DATA, ROOT, SITE

TITLE = "Anac Feed"
DESCRIPTION = (
    "Feed com notícias, vídeos e legislações publicados pela "
    "Agência Nacional de Aviação Civil (Anac)."
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
    except ValueError:
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
        published = content_item.get("iso") or datetime.now(timezone.utc).isoformat()
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


def filter_navigation(prefix=""):
    return f"""
    <nav class="filters" aria-label="Filtros de conteúdo">
      <button type="button" data-filter="all" class="active">Todos</button>
      <button type="button" data-filter="notícia">Notícias</button>
      <button type="button" data-filter="vídeo">Vídeos</button>
      <button type="button" data-filter="legislação">Legislações</button>
    </nav>
    """


def filter_script(selector):
    return f"""
    <script>
      const controls = document.querySelectorAll('[data-filter]');
      const entries = document.querySelectorAll('{selector}');
      controls.forEach((control) => {{
        control.addEventListener('click', () => {{
          const filter = control.dataset.filter;
          controls.forEach((item) => item.classList.toggle('active', item === control));
          entries.forEach((entry) => {{
            entry.hidden = filter !== 'all' && entry.dataset.type !== filter;
          }});
        }});
      }});
    </script>
    """


def write_simple_html(items):
    entries = []
    for content_item in items:
        entries.append(
            f"""
      <article class="feed-item" data-type="{esc(content_item.get('type'))}">
        <h2>
          <a href="{esc(content_item.get('link'))}" target="_blank" rel="noopener noreferrer">
            {esc(content_item.get('title'))}
          </a>
        </h2>
        <p class="meta">{esc(content_item.get('display'))} · {esc(content_item.get('type'))}</p>
        <p>{esc(content_item.get('description'))}</p>
      </article>
            """
        )

    document = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(TITLE)} · versão simples</title>
  <meta name="description" content="{esc(DESCRIPTION)}">
  <link rel="canonical" href="{esc(SITE)}data/">
  <link rel="alternate" href="rss.xml" type="application/rss+xml" title="RSS">
  <link rel="alternate" href="atom.xml" type="application/atom+xml" title="Atom">
  <link rel="alternate" href="feed.json" type="application/feed+json" title="JSON Feed">
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 1100px; margin: auto; padding: 1rem; line-height: 1.55; }}
    header, footer, .filters {{ text-align: center; }}
    .filters {{ margin: 1rem 0 2rem; }}
    button {{ margin: .3rem; padding: .55rem .9rem; cursor: pointer; }}
    button.active {{ font-weight: 700; }}
    .feed-item {{ padding: 1rem 0; border-bottom: 1px solid #ddd; }}
    .feed-item h2 {{ margin-bottom: .25rem; font-size: 1.15rem; }}
    .meta {{ color: #555; font-size: .85rem; }}
    footer {{ margin-top: 2rem; }}
    footer a {{ margin: .5rem; }}
  </style>
</head>
<body>
  <header>
    <h1>{esc(TITLE)}</h1>
    <p>{esc(DESCRIPTION)}</p>
    <p><a href="../index.html">Versão semântica</a></p>
  </header>
  {filter_navigation()}
  <main>{''.join(entries)}</main>
  <footer>
    <a href="rss.xml">RSS</a>
    <a href="atom.xml">Atom</a>
    <a href="feed.json">JSON Feed</a>
    <a href="anac_feed.json">JSON consolidado</a>
  </footer>
  {filter_script('.feed-item')}
</body>
</html>
"""
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "index.html").write_text(document, encoding="utf-8")


def write_semantic_html(items):
    cards = []
    for content_item in items:
        image = ""
        if content_item.get("image"):
            image = (
                f'<img class="article-image" src="{esc(content_item.get("image"))}" '
                f'alt="{esc(content_item.get("title"))}" loading="lazy">'
            )
        cards.append(
            f"""
      <article data-type="{esc(content_item.get('type'))}">
        {image}
        <div class="article-content">
          <div class="article-meta">
            <time datetime="{esc(content_item.get('iso'))}">{esc(content_item.get('display'))}</time>
            <span>{esc(content_item.get('type'))}</span>
          </div>
          <h2>
            <a href="{esc(content_item.get('link'))}" target="_blank" rel="noopener noreferrer">
              {esc(content_item.get('title'))}
            </a>
          </h2>
          <p>{esc(content_item.get('description'))}</p>
        </div>
      </article>
            """
        )

    document = f"""<!doctype html>
<html lang="pt-BR" vocab="https://schema.org/">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(TITLE)}</title>
  <meta name="description" content="{esc(DESCRIPTION)}">
  <link rel="canonical" href="{esc(SITE)}">
  <link rel="alternate" href="data/rss.xml" type="application/rss+xml" title="RSS">
  <link rel="alternate" href="data/atom.xml" type="application/atom+xml" title="Atom">
  <link rel="alternate" href="data/feed.json" type="application/feed+json" title="JSON Feed">
  <style>
    :root {{ --primary: #0066cc; --secondary: #004080; --dark: #212529; --success: #168821; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: system-ui, sans-serif; line-height: 1.55; background: #f5f5f5; color: var(--dark); }}
    header {{ padding: 2rem 1rem; text-align: center; color: white; background: linear-gradient(135deg, var(--primary), var(--secondary)); }}
    .container {{ max-width: 1200px; margin: auto; padding: 1rem; }}
    .filters {{ text-align: center; margin: 1rem 0 2rem; }}
    button {{ margin: .3rem; padding: .6rem 1rem; cursor: pointer; border: 0; border-radius: .3rem; color: white; background: var(--primary); }}
    button.active {{ background: var(--success); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }}
    article {{ overflow: hidden; background: white; border-radius: .4rem; box-shadow: 0 2px 10px #0002; }}
    .article-image {{ width: 100%; height: 200px; object-fit: cover; }}
    .article-content {{ padding: 1.5rem; }}
    .article-meta {{ display: flex; justify-content: space-between; color: #555; font-size: .85rem; }}
    h2 a {{ color: var(--dark); text-decoration: none; }}
    h2 a:hover {{ color: var(--primary); text-decoration: underline; }}
    footer {{ margin-top: 2rem; padding: 2rem; text-align: center; color: white; background: var(--dark); }}
    footer a {{ color: #9cf; margin: .5rem; }}
  </style>
</head>
<body>
  <header typeof="WPHeader">
    <h1>{esc(TITLE)}</h1>
    <p>{esc(DESCRIPTION)}</p>
    <p><a href="data/index.html" style="color: white">Versão simples</a></p>
  </header>
  <main class="container">
    {filter_navigation()}
    <section class="grid" aria-label="Publicações">{''.join(cards)}</section>
  </main>
  <footer>
    <a href="data/index.html">HTML simples</a>
    <a href="data/rss.xml">RSS</a>
    <a href="data/atom.xml">Atom</a>
    <a href="data/feed.json">JSON Feed</a>
    <a href="data/anac_feed.json">JSON consolidado</a>
  </footer>
  {filter_script('article[data-type]')}
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
