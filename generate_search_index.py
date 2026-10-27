import html
import json
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SITE_ROOT = ROOT / "www.alchemistcodedb.com"
OUTPUT = ROOT / "search-index.json"
CATEGORIES = {
    "card": "Memento",
    "gear": "Gear",
    "item": "Item",
    "mission": "Mission",
    "quest": "Quest",
    "rune": "Rune",
    "skill": "Skill",
    "unit": "Unit",
}
ICON_DIRECTORIES = {
    "card": ("ConceptCardIcon",),
    "gear": ("ArtiIcon",),
    "item": ("ItemIcon",),
    "mission": ("ItemIcon", "PortraitsM"),
    "quest": ("PortraitsM",),
    "rune": ("ItemIcon",),
    "skill": ("JobIcon",),
    "unit": ("PortraitsM",),
}


class PageMetadata(HTMLParser):
    def __init__(self, icon_directories):
        super().__init__()
        self.title = []
        self.description = ""
        self.in_title = False
        self.icon_directories = icon_directories
        self.icon = ""

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "meta" and attributes.get("name", "").lower() == "description":
            self.description = attributes.get("content", "")
        elif tag == "img" and not self.icon:
            src = attributes.get("src", "")
            for directory in self.icon_directories:
                marker = f"/images/{directory}/"
                if marker in src:
                    self.icon = f"{directory}/{src.split(marker, 1)[1]}"
                    break

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)


def main():
    entries = []
    for folder, category in CATEGORIES.items():
        for page in (SITE_ROOT / folder).rglob("*.html"):
            metadata = PageMetadata(ICON_DIRECTORIES[folder])
            tail = ""
            found_head = False
            with page.open(encoding="utf-8", errors="replace") as source:
                while True:
                    chunk = source.read(8192)
                    if not chunk:
                        break
                    metadata.feed(chunk)
                    head = tail + chunk.lower()
                    if "</head>" in head:
                        found_head = True
                    if found_head and metadata.icon:
                        break
                    if not found_head:
                        tail = head[-7:]
            title = html.unescape(" ".join(" ".join(metadata.title).split()))
            title = title.removesuffix(f" - {category} - The Alchemist Code").strip()
            if not title:
                continue
            relative_path = page.relative_to(SITE_ROOT).as_posix()
            entries.append({
                "title": title,
                "category": category,
                "path": relative_path,
                "slug": page.stem,
                "description": html.unescape(metadata.description),
                "icon": metadata.icon,
            })

    entries.sort(key=lambda entry: (entry["title"].casefold(), entry["category"], entry["path"]))
    OUTPUT.write_text(json.dumps(entries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(entries)} entries to {OUTPUT}")


if __name__ == "__main__":
    main()
