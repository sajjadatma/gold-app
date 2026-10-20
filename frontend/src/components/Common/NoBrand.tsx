import { Link } from "@tanstack/react-router"

import { CreateBrandDialog } from "@/components/Brand/CreateBrandDialog"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n"

export function NoBrand() {
  const { t } = useI18n()
  return (
    <div className="flex flex-col items-start gap-4 rounded-lg border border-dashed p-8">
      <div>
        <h2 className="text-lg font-semibold">
          {t("Create your first brand")}
        </h2>
        <p className="text-sm text-muted-foreground">
          {t(
            "Brand Studio works inside a jewelry brand workspace. You can create one now or open an existing brand.",
          )}
        </p>
      </div>
      <div className="flex gap-2">
        <CreateBrandDialog />
        <Button variant="outline" asChild>
          <Link to="/">{t("Choose a brand")}</Link>
        </Button>
      </div>
    </div>
  )
}
