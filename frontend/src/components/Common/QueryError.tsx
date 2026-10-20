import { AlertCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"

export function QueryError({ onRetry }: { onRetry?: () => void }) {
  const { t } = useI18n()

  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-destructive/40 bg-destructive/5 p-8 text-center">
      <AlertCircle className="h-6 w-6 text-destructive" />
      <p className="text-sm text-muted-foreground">
        {t("Could not load data. Please try again.")}
      </p>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          {t("Retry")}
        </Button>
      ) : null}
    </div>
  )
}
