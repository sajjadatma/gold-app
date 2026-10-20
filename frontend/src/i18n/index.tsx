import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react"

import { fa } from "./fa"

export type Language = "en" | "fa"

const STORAGE_KEY = "app_language"

type Vars = Record<string, string | number>

type I18nContextValue = {
  language: Language
  dir: "ltr" | "rtl"
  locale: string
  setLanguage: (language: Language) => void
  t: (key: string, vars?: Vars) => string
  formatDate: (
    value: string | number | Date,
    options?: Intl.DateTimeFormatOptions,
  ) => string
}

const I18nContext = createContext<I18nContextValue | null>(null)

function initialLanguage(): Language {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === "fa" || saved === "en") return saved
  return navigator.language.toLowerCase().startsWith("fa") ? "fa" : "en"
}

function interpolate(template: string, vars?: Vars): string {
  if (!vars) return template
  return template.replace(/\{(\w+)\}/g, (_match, key: string) =>
    vars[key] === undefined ? `{${key}}` : String(vars[key]),
  )
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(initialLanguage)
  const dir = language === "fa" ? "rtl" : "ltr"
  const locale = language === "fa" ? "fa-IR" : "en-US"

  useEffect(() => {
    document.documentElement.lang = language
    document.documentElement.dir = dir
  }, [language, dir])

  const setLanguage = useCallback((next: Language) => {
    localStorage.setItem(STORAGE_KEY, next)
    setLanguageState(next)
  }, [])

  const t = useCallback(
    (key: string, vars?: Vars) => {
      const template = language === "fa" ? (fa[key] ?? key) : key
      return interpolate(template, vars)
    },
    [language],
  )

  const formatDate = useCallback(
    (
      value: string | number | Date,
      options: Intl.DateTimeFormatOptions = {
        year: "numeric",
        month: "short",
        day: "numeric",
      },
    ) =>
      new Intl.DateTimeFormat(locale, options).format(
        value instanceof Date ? value : new Date(value),
      ),
    [locale],
  )

  const value = useMemo(
    () => ({
      language,
      dir: dir as "ltr" | "rtl",
      locale,
      setLanguage,
      t,
      formatDate,
    }),
    [language, dir, locale, setLanguage, t, formatDate],
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error("useI18n must be used within I18nProvider")
  }
  return context
}

export function pageTitle(english: string, farsi: string): string {
  const saved = localStorage.getItem(STORAGE_KEY)
  const language =
    saved === "fa" || saved === "en"
      ? saved
      : navigator.language.toLowerCase().startsWith("fa")
        ? "fa"
        : "en"
  return language === "fa" ? farsi : english
}
