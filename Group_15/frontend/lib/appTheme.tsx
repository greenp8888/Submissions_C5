"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

export const APP_THEME_STORAGE_KEY = "signalforge-theme";

type ThemeContextValue = {
  isDark: boolean;
  setIsDark: (dark: boolean) => void;
  toggleTheme: () => void;
  /** True after reading localStorage on the client (for SSR/hydration-safe UI). */
  mounted: boolean;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

function readStoredIsDark(): boolean {
  if (typeof window === "undefined") return true;
  try {
    return window.localStorage.getItem(APP_THEME_STORAGE_KEY) !== "light";
  } catch {
    return true;
  }
}

export function AppThemeProvider({ children }: { children: React.ReactNode }) {
  const [isDark, setIsDarkState] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setIsDarkState(readStoredIsDark());
    setMounted(true);
  }, []);

  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key !== APP_THEME_STORAGE_KEY || e.newValue == null) return;
      setIsDarkState(e.newValue !== "light");
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const setIsDark = useCallback((dark: boolean) => {
    setIsDarkState(dark);
    try {
      window.localStorage.setItem(APP_THEME_STORAGE_KEY, dark ? "dark" : "light");
    } catch {
      /* ignore */
    }
  }, []);

  const toggleTheme = useCallback(() => {
    setIsDarkState((prev) => {
      const next = !prev;
      try {
        window.localStorage.setItem(APP_THEME_STORAGE_KEY, next ? "dark" : "light");
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  const value = useMemo(
    () => ({ isDark, setIsDark, toggleTheme, mounted }),
    [isDark, setIsDark, toggleTheme, mounted]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useAppTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useAppTheme must be used within AppThemeProvider");
  }
  return ctx;
}
