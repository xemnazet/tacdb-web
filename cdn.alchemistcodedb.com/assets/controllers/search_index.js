const indexUrls = {
  en: new URL("../../../search-index.json", import.meta.url),
  jp: new URL("../../../search-index-jp.json", import.meta.url),
};
export const siteRoot = new URL("../../../www.alchemistcodedb.com/", import.meta.url);

const japaneseCategories = {
  Crystal: "幻影記憶",
  Gear: "ギア",
  Item: "アイテム",
  Memento: "真理念装",
  Mission: "ミッション",
  Quest: "クエスト",
  Rune: "真理刻印",
  Skill: "スキル",
  Unit: "ユニット",
};

const indexPromises = new Map();

export function loadSearchIndex(locale = "en") {
  if (!indexPromises.has(locale)) {
    const indexUrl = indexUrls[locale] || indexUrls.en;
    const indexPromise = fetch(indexUrl, { cache: "no-cache" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Search index request failed: ${response.status}`);
        }
        return response.json();
      })
      .catch((error) => {
        indexPromises.delete(locale);
        throw error;
      });
    indexPromises.set(locale, indexPromise);
  }
  return indexPromises.get(locale);
}

function normalize(value) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
}

export function categoryLabel(category, locale = "en") {
  return locale === "jp" ? japaneseCategories[category] || category : category;
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
      const searchableText = normalize([entry.title, entry.slug, entry.description].filter(Boolean).join(" "));
      if (!terms.every((term) => searchableText.includes(term))) {
        return null;
      }

      const titleRank = title === normalizedQuery ? 0
        : title.startsWith(normalizedQuery) ? 1
        : title.includes(normalizedQuery) ? 2
        : 5;
      const rank = titleRank < 5
        ? titleRank
        : slug.startsWith(normalizedQuery) ? 3 : 4;
      return {
        entry: {
          ...entry,
        },
        rank,
      };
    })
    .filter(Boolean)
    .sort((left, right) => left.rank - right.rank
      || left.entry.title.localeCompare(right.entry.title))
    .slice(0, limit)
    .map(({ entry }) => entry);
}
