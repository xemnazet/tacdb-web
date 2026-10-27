import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SITE_ROOT = ROOT / "www.alchemistcodedb.com"
SEARCH_SCRIPT = ROOT / "cdn.alchemistcodedb.com" / "assets" / "local_search.js"
LISTING_SEARCH_SCRIPT = ROOT / "cdn.alchemistcodedb.com" / "assets" / "local_listing_search.js"
SEARCH_FORM = re.compile(r'<form id="search"[^>]*>.*?</form>', re.IGNORECASE | re.DOTALL)
CATEGORY_SEARCH_FORM = re.compile(
    r'<form\b(?=[^>]*\bid=["\'](?:jp_)?(?:card|crystal|gear|item|mission|quest|rune|skill|unit)_search["\'])[^>]*>',
    re.IGNORECASE,
)
INDEX_LISTING = re.compile(r'<turbo-frame\b(?=[^>]*\bid=["\']index_listing["\'])', re.IGNORECASE)
SEARCH_ATTRIBUTES = re.compile(
    r'\sdata-controller="search"'
    r'|\sdata-search-target="[^"]*"'
    r'|\sdata-action="[^"]*search#[^"]*"',
    re.IGNORECASE,
)
FORM_ACTION = re.compile(r'\saction=(["\']).*?\1', re.IGNORECASE)
SEARCH_INPUT = re.compile(r'(<input\b(?=[^>]*\bname=["\']s["\'])[^>]*)(/?>)', re.IGNORECASE)
BODY_END = re.compile(r"</body\s*>", re.IGNORECASE)


def prepare_page(page, dry_run=False):
    with page.open(encoding="utf-8", errors="replace", newline="") as page_file:
        source = page_file.read()
    match = SEARCH_FORM.search(source)
    has_listing_search = CATEGORY_SEARCH_FORM.search(source) and INDEX_LISTING.search(source)
    if not match and not has_listing_search:
        return False

    updated = source
    if match:
        relative_page = page.relative_to(SITE_ROOT)
        is_japanese_page = (
            relative_page.parts[0].lower() == "jp"
            or page.name.lower() == "jp.html"
            or re.search(r'<body\b[^>]*\bdata-locale="jp"', source, re.IGNORECASE) is not None
        )
        result_page = SITE_ROOT / ("jp" if is_japanese_page else "") / "search.html"
        relative_search_page = os.path.relpath(result_page, page.parent).replace(os.sep, "/")
        form = match.group(0)
        form = SEARCH_ATTRIBUTES.sub("", form)
        form, replacements = FORM_ACTION.subn(f' action="{relative_search_page}"', form, count=1)
        if not replacements:
            form = re.sub(r"<form\b", f'<form action="{relative_search_page}"', form, count=1, flags=re.IGNORECASE)
        form = SEARCH_INPUT.sub(
            lambda input_match: input_match.group(0)
            if re.search(r"\srequired(?:\s|=|/?>)", input_match.group(0), re.IGNORECASE)
            else f"{input_match.group(1)} required{input_match.group(2)}",
            form,
            count=1,
        )
        updated = updated[:match.start()] + form + updated[match.end():]

    scripts = []
    if match:
        relative_script = os.path.relpath(SEARCH_SCRIPT, page.parent).replace(os.sep, "/")
        scripts.append(f'<script type="module" src="{relative_script}"></script>')
    if has_listing_search:
        relative_listing_script = os.path.relpath(LISTING_SEARCH_SCRIPT, page.parent).replace(os.sep, "/")
        scripts.append(f'<script type="module" src="{relative_listing_script}"></script>')
    scripts = [script for script in scripts if script not in updated]
    if scripts:
        script_markup = "\n".join(scripts) + "\n</body>"
        updated, replacements = BODY_END.subn(script_markup, updated, count=1)
        if not replacements:
            raise ValueError(f"Cannot add local search to page without a body end tag: {page}")

    if updated != source:
        if not dry_run:
            with page.open("w", encoding="utf-8", newline="") as page_file:
                page_file.write(updated)
        return True
    return False


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Report pages that need changes without writing them")
    args = parser.parse_args()
    changed = 0
    for page in SITE_ROOT.rglob("*.html"):
        changed += prepare_page(page, dry_run=args.check)
    action = "would prepare" if args.check else "prepared"
    print(f"{action.capitalize()} local header search on {changed} pages.")


if __name__ == "__main__":
    main()
