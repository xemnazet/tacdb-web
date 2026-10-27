import html
import json
import posixpath
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SITE_ROOT = ROOT / "www.alchemistcodedb.com"
OUTPUT = ROOT / "search-index.json"
JP_OUTPUT = ROOT / "search-index-jp.json"
CATEGORIES = {
    "card": "Memento",
    "crystal": "Crystal",
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
    "crystal": ("CrystalIcon",),
    "gear": ("ArtiIcon",),
    "item": ("ItemIcon",),
    "mission": ("ItemIcon", "PortraitsM"),
    "quest": ("PortraitsM",),
    "rune": ("ItemIcon",),
    "skill": ("JobIcon",),
    "unit": ("PortraitsM",),
}
LISTING_DIRECTORIES = {
    "card": "cards",
    "crystal": "crystals",
    "gear": "gears",
    "item": "items",
    "mission": "missions",
    "quest": "quests",
    "rune": "runes",
    "skill": "skills",
    "unit": "units",
}


class ListingElement:
    def __init__(self, tag, attrs, start, inside_listing):
        self.tag = tag
        self.attrs = dict(attrs)
        self.start = start
        self.hrefs = []
        self.inside_listing = inside_listing


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


def read_page_metadata(page, folder):
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
    return metadata


def clean_title(metadata, category, japanese=False):
    title = html.unescape(" ".join(" ".join(metadata.title).split()))
    if japanese:
        return title.split(" - ", 1)[0].strip()
    return title.removesuffix(f" - {category} - The Alchemist Code").strip()


class ListingParser(HTMLParser):
    def __init__(self, source, source_path, entries_by_path, category):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.source_path = source_path
        self.entries_by_path = entries_by_path
        self.category = category
        self.line_offsets = [0]
        for line in source.splitlines(keepends=True):
            self.line_offsets.append(self.line_offsets[-1] + len(line))
        self.stack = []

    def source_offset(self):
        line, column = self.getpos()
        return self.line_offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        inside_listing = (
            self.stack[-1].inside_listing if self.stack
            else False
        ) or dict(attrs).get("id") == "index_listing"
        element = ListingElement(tag, attrs, self.source_offset(), inside_listing)
        self.stack.append(element)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].tag == tag:
                element = self.stack[index]
                del self.stack[index:]
                end = self.source.find(">", self.source_offset()) + 1
                self.finish_element(element, end)
                return

    def finish_element(self, element, end):
        classes = element.attrs.get("class", "").split()
        is_listing_column = element.tag == "div" and any(
            class_name.startswith("col-") for class_name in classes
        )
        if element.inside_listing and (element.tag == "tr" or is_listing_column):
            for path in element.hrefs:
                entry = self.entries_by_path.get(path)
                if entry and entry["category"] == self.category and not entry.get("listingHtml"):
                    entry["listingHtml"] = self.source[element.start:end]
                    entry["listingBase"] = self.source_path
                    break

        href = element.attrs.get("href")
        if element.tag == "a" and href:
            href_path = html.unescape(href).split("#", 1)[0].split("?", 1)[0]
            if href_path and not href_path.startswith(("http:", "https:", "javascript:", "#")):
                path = posixpath.normpath(posixpath.join(
                    posixpath.dirname(self.source_path),
                    href_path,
                ))
                element.hrefs.append(path)

        if self.stack:
            self.stack[-1].hrefs.extend(element.hrefs)


def add_listing_markup(entries, source_root, japanese=False):
    entries_by_path = {entry["path"]: entry for entry in entries}
    for folder, category in CATEGORIES.items():
        listing_directory = source_root / LISTING_DIRECTORIES[folder]
        list_pages = []
        index_page = listing_directory.with_suffix(".html")
        if index_page.is_file():
            list_pages.append(index_page)
        if listing_directory.is_dir():
            list_pages.extend(listing_directory.rglob("*.html"))

        for page in list_pages:
            source_path = page.relative_to(SITE_ROOT).as_posix()
            source = page.read_text(encoding="utf-8", errors="replace")
            parser = ListingParser(source, source_path, entries_by_path, category)
            parser.feed(source)


def build_entries(source_root, japanese=False):
    entries = []
    for folder, category in CATEGORIES.items():
        for page in (source_root / folder).rglob("*.html"):
            metadata = read_page_metadata(page, folder)
            title = clean_title(metadata, category, japanese=japanese)
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
    add_listing_markup(entries, source_root, japanese=japanese)
    return entries


def write_index(output, entries):
    output.write_text(json.dumps(entries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(entries)} entries to {output}")


def main():
    write_index(OUTPUT, build_entries(SITE_ROOT))
    write_index(JP_OUTPUT, build_entries(SITE_ROOT / "jp", japanese=True))


if __name__ == "__main__":
    main()
