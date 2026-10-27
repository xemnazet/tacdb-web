const indexUrl = new URL("../../../search-index.json", import.meta.url);
export const siteRoot = new URL("../../../www.alchemistcodedb.com/", import.meta.url);

let indexPromise;

export function loadSearchIndex() {
  if (!indexPromise) {
    indexPromise = fetch(indexUrl)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Search index request failed: ${response.status}`);
        }
        return response.json();
      })
      .catch((error) => {
        indexPromise = undefined;
        throw error;
      });
  }
  return indexPromise;
}

function normalize(value) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
}

export function searchEntries(entries, query, limit = 10) {
  const normalizedQuery = normalize(query.trim());
  if (!normalizedQuery) {
    return [];
  }

  const terms = normalizedQuery.split(/\s+/);
  return entries
    .map((entry) => {
      const title = normalize(entry.title);
      const slug = normalize(entry.slug);
      const searchableText = normalize(`${entry.title} ${entry.slug} ${entry.description}`);
      if (!terms.every((term) => searchableText.includes(term))) {
        return null;
      }

      const rank = title === normalizedQuery ? 0
        : title.startsWith(normalizedQuery) ? 1
        : title.includes(normalizedQuery) ? 2
        : slug.startsWith(normalizedQuery) ? 3
        : 4;
      return { entry, rank };
    })
    .filter(Boolean)
    .sort((left, right) => left.rank - right.rank
      || left.entry.title.localeCompare(right.entry.title))
    .slice(0, limit)
    .map(({ entry }) => entry);
}
