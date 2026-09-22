import { useSyncExternalStore } from "react";
import type { TranslationResponse } from "../types";

const STORAGE_KEY = "translation_results";
const CHANGE_EVENT = "translation_results_changed";

export interface StoredResult extends TranslationResponse {
  id: string;
  created_at: string;
}

const EMPTY: StoredResult[] = [];

let cache: StoredResult[] | null = null;

function loadFromStorage(): StoredResult[] {
  if (typeof window === "undefined") return EMPTY;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as StoredResult[]) : EMPTY;
  } catch {
    return EMPTY;
  }
}

function getSnapshot(): StoredResult[] {
  if (cache === null) {
    cache = loadFromStorage();
  }
  return cache;
}

function getServerSnapshot(): StoredResult[] {
  return EMPTY;
}

function commit(items: StoredResult[]): void {
  cache = items;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    window.dispatchEvent(new Event(CHANGE_EVENT));
  }
}

function makeId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function addResult(result: TranslationResponse): StoredResult {
  const stored: StoredResult = {
    ...result,
    id: makeId(),
    created_at: new Date().toISOString(),
  };
  commit([stored, ...getSnapshot()]);
  return stored;
}

export function addResults(results: TranslationResponse[]): StoredResult[] {
  if (!results.length) return [];
  const stored: StoredResult[] = results.map((result) => ({
    ...result,
    id: makeId(),
    created_at: new Date().toISOString(),
  }));
  commit([...stored, ...getSnapshot()]);
  return stored;
}

export function deleteResult(id: string): void {
  commit(getSnapshot().filter((r) => r.id !== id));
}

export function clearResults(): void {
  commit([]);
}

function subscribe(callback: () => void): () => void {
  const handler = () => {
    cache = loadFromStorage();
    callback();
  };
  window.addEventListener(CHANGE_EVENT, handler);
  window.addEventListener("storage", handler);
  return () => {
    window.removeEventListener(CHANGE_EVENT, handler);
    window.removeEventListener("storage", handler);
  };
}

export function useResults(): StoredResult[] {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
