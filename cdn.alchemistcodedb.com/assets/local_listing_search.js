import { categoryLabel, loadSearchIndex, searchEntries, siteRoot } from "./controllers/search_index.js";

const categoryByForm = {
  card: "Memento",
  crystal: "Crystal",
  gear: "Gear",
  item: "Item",
  mission: "Mission",
  quest: "Quest",
  rune: "Rune",
  skill: "Skill",
  unit: "Unit",
};

const form = document.querySelector("form[id$='_search']");
const match = form?.id.match(/^(?:jp_)?(card|crystal|gear|item|mission|quest|rune|skill|unit)_search$/);
const input = form?.querySelector('input[name="q[name_cont]"]');
const listing = document.getElementById("index_listing");

if (match && input && listing) {
  const locale = document.body.dataset.locale === "jp" ? "jp" : "en";
  const category = categoryByForm[match[1]];
  const originalListing = listing.innerHTML;
  const status = document.createElement("p");
  status.className = "px-3 pt-3 mb-0";
  status.setAttribute("role", "status");
  let searchVersion = 0;
  form.action = window.location.href.split("?")[0];
  form.dataset.turbo = "false";

  function appendResult(result, resultContainer, table, fallbackRow, fallbackColumnClass) {
    if (result.listingHtml && result.listingBase) {
      const itemTemplate = document.createElement("template");
      itemTemplate.innerHTML = result.listingHtml;
      for (const element of itemTemplate.content.querySelectorAll("[href], [src]")) {
        for (const attribute of ["href", "src"]) {
          const value = element.getAttribute(attribute);
          if (value && !/^(?:[a-z]+:|#|\/\/)/i.test(value)) {
            const base = new URL(result.listingBase, siteRoot);
            element.setAttribute(attribute, new URL(value, base).href);
          }
        }
      }
      resultContainer.append(itemTemplate.content);
      return;
    }

    if (table) {
      if (!fallbackRow) {
        return;
      }
      const row = fallbackRow.cloneNode(true);
      const link = row.querySelector("a");
      if (link) {
        link.href = new URL(result.path, siteRoot).href;
        link.textContent = result.title;
      }
      const icon = row.querySelector("img");
      if (icon && result.icon) {
        icon.src = new URL(`../cdn.alchemistcodedb.com/images/${result.icon}`, siteRoot).href;
      }
      for (const cell of row.querySelectorAll("td:not(:first-child)")) {
        cell.replaceChildren();
      }
      resultContainer.append(row);
      return;
    }

    const column = document.createElement("div");
    column.className = fallbackColumnClass || "col-lg-6 d-flex";
    const link = document.createElement("a");
    link.className = "listing-link d-flex";
    link.href = new URL(result.path, siteRoot).href;
    const card = document.createElement("div");
    card.className = "d-flex index-list-item flex-fill";
    if (result.icon) {
      const iconContainer = document.createElement("div");
      iconContainer.className = `${category.toLowerCase()}-icon me-3`;
      const icon = document.createElement("img");
      icon.className = "tiny-img";
      icon.src = new URL(`../cdn.alchemistcodedb.com/images/${result.icon}`, siteRoot).href;
      icon.alt = "";
      icon.loading = "lazy";
      iconContainer.append(icon);
      card.append(iconContainer);
    }
    const content = document.createElement("div");
    content.className = "flex-grow-1";
    const heading = document.createElement("div");
    heading.className = "gear-heading";
    const title = document.createElement("h5");
    title.textContent = result.title;
    heading.append(title);
    content.append(heading);
    if (result.description) {
      const details = document.createElement("div");
      details.className = "gear-details";
      const description = document.createElement("div");
      description.className = "gear-detail-box";
      description.textContent = result.description;
      details.append(description);
      content.append(details);
    }
    card.append(content);
    link.append(card);
    column.append(link);
    resultContainer.append(column);
  }

  async function updateListing() {
    const query = input.value.trim();
    const version = ++searchVersion;
    if (!query) {
      listing.innerHTML = originalListing;
      return;
    }

    status.textContent = locale === "jp" ? "検索しています…" : "Searching this category…";
    listing.replaceChildren(status);

    try {
      const entries = await loadSearchIndex(locale);
      if (version !== searchVersion) {
        return;
      }

      const results = searchEntries(
        entries.filter((entry) => entry.category === category),
        query,
        1000,
      );
      const template = document.createElement("template");
      template.innerHTML = originalListing;
      const table = template.content.querySelector("table.index-table");
      const resultContainer = table
        ? table.querySelector("tbody")
        : template.content.querySelector(".card-body .row");
      if (!resultContainer) {
        throw new Error(`Could not find the original ${category} listing container.`);
      }

      const fallbackRow = table ? resultContainer.querySelector("tr")?.cloneNode(true) : null;
      const fallbackColumnClass = resultContainer.firstElementChild?.className;
      resultContainer.replaceChildren();
      for (const result of results) {
        appendResult(result, resultContainer, table, fallbackRow, fallbackColumnClass);
      }

      status.textContent = results.length
        ? locale === "jp"
          ? `${results.length === 1000 ? "最初の1000件を表示" : `${results.length}件`}： “${query}” の検索結果`
          : `${results.length === 1000 ? "Showing the first 1000" : results.length} results for “${query}”.`
        : locale === "jp"
          ? `“${query}” に一致する${categoryLabel(category, locale)}はありません。`
          : `No ${category.toLowerCase()} results found for “${query}”.`;
      listing.replaceChildren(status, template.content);
    } catch (error) {
      if (version !== searchVersion) {
        return;
      }
      console.error("Could not load local category search data.", error);
      status.textContent = locale === "jp"
        ? "検索データを読み込めませんでした。"
        : "Search data could not be loaded.";
    }
  }

  form.addEventListener("submit", (event) => {
    if (event.submitter?.closest("#filtersModal")) {
      return;
    }
    event.preventDefault();
    updateListing();
  }, true);

  input.addEventListener("input", updateListing);
}
