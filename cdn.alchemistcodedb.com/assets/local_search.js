import { categoryLabel, loadSearchIndex, searchEntries, siteRoot } from "./controllers/search_index.js";

const form = document.getElementById("search");
const input = form?.querySelector('input[name="s"]');
const list = document.getElementById("search_list");
const loading = form?.querySelector(".search-loading");

if (form && input && list && loading) {
  const locale = document.body.dataset.locale === "jp" ? "jp" : "en";
  const searchPage = locale === "jp" ? "jp/search.html" : "search.html";
  form.action = new URL(searchPage, siteRoot).href;
  let timeout;
  let searchVersion = 0;

  input.addEventListener("input", () => {
    const version = ++searchVersion;
    clearTimeout(timeout);
    list.replaceChildren();
    list.hidden = true;
    loading.classList.add("d-none");

    if (!input.value.trim()) {
      return;
    }

    loading.classList.remove("d-none");
    timeout = setTimeout(async () => {
      try {
        const entries = await loadSearchIndex(locale);
        if (version !== searchVersion) {
          return;
        }

        for (const result of searchEntries(entries, input.value, 10)) {
          const item = document.createElement("li");
          item.setAttribute("role", "option");
          const link = document.createElement("a");
          link.href = new URL(result.path, siteRoot).href;
          link.textContent = `${result.title} (${categoryLabel(result.category, locale)})`;
          item.append(link);
          list.append(item);
        }
      } catch (error) {
        if (version !== searchVersion) {
          return;
        }
        console.error("Could not load local search data.", error);
        const item = document.createElement("li");
        item.setAttribute("role", "option");
        item.textContent = "Search data could not be loaded.";
        list.append(item);
      } finally {
        if (version === searchVersion) {
          loading.classList.add("d-none");
          list.hidden = !list.querySelector("li");
        }
      }
    }, 250);
  });

  input.addEventListener("focus", () => {
    if (list.querySelector("li")) {
      list.hidden = false;
    }
  });

  input.addEventListener("blur", () => {
    window.setTimeout(() => {
      list.hidden = true;
    }, 150);
  });
}
