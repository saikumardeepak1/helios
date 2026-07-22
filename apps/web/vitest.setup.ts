import "@testing-library/jest-dom/vitest";

// Newer Node versions ship an experimental native `localStorage` that can
// collide with jsdom's own implementation depending on load order, leaving
// window.localStorage as a stub that throws on setItem/clear. Replace it
// with a small, reliable in-memory implementation for tests.
class MemoryStorage implements Storage {
  private store = new Map<string, string>();

  get length() {
    return this.store.size;
  }

  clear(): void {
    this.store.clear();
  }

  getItem(key: string): string | null {
    return this.store.has(key) ? this.store.get(key)! : null;
  }

  key(index: number): string | null {
    return Array.from(this.store.keys())[index] ?? null;
  }

  removeItem(key: string): void {
    this.store.delete(key);
  }

  setItem(key: string, value: string): void {
    this.store.set(key, String(value));
  }
}

const memoryStorage = new MemoryStorage();

for (const target of [globalThis, window]) {
  Object.defineProperty(target, "localStorage", {
    value: memoryStorage,
    writable: true,
    configurable: true,
  });
}

// jsdom doesn't implement ResizeObserver; Recharts' ResponsiveContainer needs it.
class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

for (const target of [globalThis, window]) {
  Object.defineProperty(target, "ResizeObserver", {
    value: ResizeObserverStub,
    writable: true,
    configurable: true,
  });
}
