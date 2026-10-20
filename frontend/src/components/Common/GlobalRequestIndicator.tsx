import { useIsFetching, useIsMutating } from "@tanstack/react-query"

import { useI18n } from "@/i18n"

export function GlobalRequestIndicator() {
  const { t } = useI18n()
  const initialLoads = useIsFetching({
    predicate: (query) =>
      query.state.fetchStatus === "fetching" && query.state.data === undefined,
  })
  const mutations = useIsMutating()
  const active = initialLoads + mutations > 0

  if (!active) return null

  return (
    <div
      role="status"
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 top-0 z-[100] h-0.5 overflow-hidden bg-primary/20"
    >
      <div className="h-full w-full animate-pulse bg-primary" />
      <span className="sr-only">{t("Loading")}</span>
    </div>
  )
}
