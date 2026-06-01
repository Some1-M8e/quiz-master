// Entfernt Zusätze wie "#18" oder "– Staffel 4" aus dem Eventtitel
export function displayTitle(title) {
  return title.replace(/\s+(#\S+|[–—].+)$/, "").trim();
}
