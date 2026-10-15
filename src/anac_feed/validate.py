import json
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from .config import DATA, ROOT


class Validator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.errors = []
        self.articles = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "a" and not values.get("href"):
            self.errors.append("link sem href")
        if tag == "img":
            if not values.get("src"):
                self.errors.append("imagem sem src")
            if "alt" not in values:
                self.errors.append("imagem sem alt")
        if tag == "article":
            self.articles += 1


def validate(expected):
    semantic = ROOT / "index.html"
    simple = DATA / "index.html"
    json_feed = DATA / "feed.json"
    rss = DATA / "rss.xml"
    atom = DATA / "atom.xml"
    consolidated = DATA / "anac_feed.json"
    paths = [semantic, simple, json_feed, rss, atom, consolidated]

    for path in paths:
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"Arquivo inválido: {path}")

    for path in (semantic, simple):
        validator = Validator()
        validator.feed(path.read_text(encoding="utf-8"))
        if validator.errors:
            raise RuntimeError(f"{path}: {validator.errors}")

    semantic_text = semantic.read_text(encoding="utf-8")
    simple_text = simple.read_text(encoding="utf-8")

    semantic_required = (
        'href="data/index.html"',
        'href="data/rss.xml"',
        'href="data/atom.xml"',
        'href="data/feed.json"',
        'href="data/anac_feed.json"',
    )
    simple_required = (
        'href="../index.html"',
        'href="rss.xml"',
        'href="atom.xml"',
        'href="feed.json"',
        'href="anac_feed.json"',
    )
    for fragment in semantic_required:
        if fragment not in semantic_text:
            raise RuntimeError(f"Fragmento ausente no HTML semântico: {fragment}")
    for fragment in simple_required:
        if fragment not in simple_text:
            raise RuntimeError(f"Fragmento ausente no HTML simples: {fragment}")

    payload = json.loads(json_feed.read_text(encoding="utf-8"))
    if payload.get("count") != expected:
        raise RuntimeError("Contagem JSON divergente")

    ET.parse(rss)
    ET.parse(atom)
    return paths
