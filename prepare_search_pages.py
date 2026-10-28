import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit


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
URL_ATTRIBUTE = re.compile(
    r'\b(?:href|src|action|poster|data-src|data-original)=(["\'])(.*?)\1',
    re.IGNORECASE | re.DOTALL,
)
BODY_END = re.compile(r"</body\s*>", re.IGNORECASE)
IMPORT_MAP = re.compile(
    r'(<script\b(?=[^>]*\btype=["\']importmap["\'])[^>]*>)(.*?)(</script\s*>)',
    re.IGNORECASE | re.DOTALL,
)
IGNORED_COPY_DIRECTORIES = shutil.ignore_patterns("__pycache__", "*.pyc")


def prepare_page(
    page,
    dry_run=False,
    site_root=SITE_ROOT,
    search_script=SEARCH_SCRIPT,
    listing_search_script=LISTING_SEARCH_SCRIPT,
):
    with page.open(encoding="utf-8", errors="replace", newline="") as page_file:
        source = page_file.read()
    match = SEARCH_FORM.search(source)
    has_listing_search = CATEGORY_SEARCH_FORM.search(source) and INDEX_LISTING.search(source)
    if not match and not has_listing_search:
        return False

    updated = source
    if match:
        relative_page = page.relative_to(site_root)
        is_japanese_page = (
            relative_page.parts[0].lower() == "jp"
            or page.name.lower() == "jp.html"
            or re.search(r'<body\b[^>]*\bdata-locale="jp"', source, re.IGNORECASE) is not None
        )
        result_page = site_root / ("jp" if is_japanese_page else "") / "search.html"
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
        relative_script = os.path.relpath(search_script, page.parent).replace(os.sep, "/")
        scripts.append(f'<script type="module" src="{relative_script}"></script>')
    if has_listing_search:
        relative_listing_script = os.path.relpath(listing_search_script, page.parent).replace(os.sep, "/")
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


def rebase_site_references(source_page, output_page, output_root):
    with output_page.open(encoding="utf-8", errors="replace", newline="") as page_file:
        source = page_file.read()

    def local_mirror_url(value):
        parsed = urlsplit(value)
        if parsed.scheme and parsed.netloc:
            mirror_root = output_root / parsed.netloc
            mirror_target = (mirror_root / unquote(parsed.path.lstrip("/"))).resolve()
            try:
                mirror_target.relative_to(mirror_root.resolve())
            except ValueError:
                return value
            if not mirror_target.exists():
                return value
            relative_url = Path(os.path.relpath(mirror_target, output_page.parent)).as_posix()
            if not relative_url.startswith("."):
                relative_url = "./" + relative_url
            return urlunsplit(("", "", quote(relative_url, safe="/.-_~"), parsed.query, parsed.fragment))

        if parsed.scheme or parsed.netloc or not parsed.path.startswith("../"):
            return value
        source_target = (source_page.parent / unquote(parsed.path)).resolve()
        try:
            relative_target = source_target.relative_to(ROOT.resolve())
        except ValueError:
            return value

        if SITE_ROOT.resolve() in source_target.parents:
            if SITE_ROOT.name not in Path(unquote(parsed.path)).parts:
                return value
            relative_target = source_target.relative_to(SITE_ROOT.resolve())

        output_target = output_root / relative_target
        if not output_target.exists():
            return value

        relative_url = Path(os.path.relpath(output_target, output_page.parent)).as_posix()
        if not relative_url.startswith("."):
            relative_url = "./" + relative_url
        return urlunsplit(("", "", quote(relative_url, safe="/.-_~"), parsed.query, parsed.fragment))

    def rebase(match):
        value = match.group(2)
        rebased_url = local_mirror_url(value)
        if rebased_url == value:
            return match.group(0)
        return match.group(0).replace(value, rebased_url, 1)

    updated = URL_ATTRIBUTE.sub(rebase, source)
    def rewrite_import_map(match):
        try:
            import_map = json.loads(match.group(2))
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid import map in {source_page}: {error}") from error

        imports = import_map.get("imports", {})
        for specifier, address in imports.items():
            if isinstance(address, str):
                imports[specifier] = local_mirror_url(address)
        return match.group(1) + json.dumps(import_map, separators=(",", ":")) + match.group(3)

    updated = IMPORT_MAP.sub(rewrite_import_map, updated)
    if updated != source:
        with output_page.open("w", encoding="utf-8", newline="") as page_file:
            page_file.write(updated)


def build_flat_site(output_dir):
    output_dir = Path(output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir = output_dir.resolve()
    if output_dir == ROOT.resolve() or ROOT.resolve() not in output_dir.parents:
        raise ValueError(f"Output directory must be a child of the repository root: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory must be empty: {output_dir}")

    excluded = {
        ".git",
        ".github",
        SITE_ROOT.name,
        output_dir.name,
        "__pycache__",
        "generate_search_index.py",
        "prepare_search_pages.py",
        "index.html",
    }
    for source in ROOT.iterdir():
        if source.name in excluded or source.suffix == ".py":
            continue
        destination = output_dir / source.name
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True, ignore=IGNORED_COPY_DIRECTORIES)
        else:
            shutil.copy2(source, destination)

    shutil.copytree(SITE_ROOT, output_dir, dirs_exist_ok=True, ignore=IGNORED_COPY_DIRECTORIES)

    for source_page in SITE_ROOT.rglob("*.html"):
        relative_page = source_page.relative_to(SITE_ROOT)
        output_page = output_dir / relative_page
        rebase_site_references(source_page, output_page, output_dir)
        prepare_page(
            output_page,
            site_root=output_dir,
            search_script=output_dir / "cdn.alchemistcodedb.com" / "assets" / "local_search.js",
            listing_search_script=output_dir / "cdn.alchemistcodedb.com" / "assets" / "local_listing_search.js",
        )

    search_index_script = output_dir / "cdn.alchemistcodedb.com" / "assets" / "controllers" / "search_index.js"
    with search_index_script.open(encoding="utf-8", errors="replace", newline="") as script_file:
        script = script_file.read()
    script = script.replace(
        'new URL("../../../www.alchemistcodedb.com/", import.meta.url)',
        'new URL("../../../", import.meta.url)',
    )
    with search_index_script.open("w", encoding="utf-8", newline="") as script_file:
        script_file.write(script)

    if not (output_dir / "index.html").is_file():
        raise FileNotFoundError(f"Flattened site is missing its root index.html: {output_dir}")
    print(f"Prepared flattened site at {output_dir}")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Report pages that need changes without writing them")
    parser.add_argument("--output-dir", type=Path, help="Build a flattened deployable site in this directory")
    args = parser.parse_args()
    if args.output_dir:
        if args.check:
            parser.error("--check cannot be combined with --output-dir")
        build_flat_site(args.output_dir)
        return
    changed = 0
    for page in SITE_ROOT.rglob("*.html"):
        changed += prepare_page(page, dry_run=args.check)
    action = "would prepare" if args.check else "prepared"
    print(f"{action.capitalize()} local header search on {changed} pages.")


if __name__ == "__main__":
    main()
