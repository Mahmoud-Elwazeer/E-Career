import { useState, useCallback } from "react";

const STORAGE_KEY = "usam-recent-searches";
const MAX_ITEMS = 5;

function load(): string[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

export function useRecentSearches() {
  const [items, setItems] = useState<string[]>(load);

  const add = useCallback((query: string) => {
    const q = query.trim();
    if (!q) return;
    setItems((prev) => {
      const deduped = prev.filter((s) => s.toLowerCase() !== q.toLowerCase());
      const next = [q, ...deduped].slice(0, MAX_ITEMS);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const clear = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setItems([]);
  }, []);

  return { recentSearches: items, addRecentSearch: add, clearRecentSearches: clear };
}
