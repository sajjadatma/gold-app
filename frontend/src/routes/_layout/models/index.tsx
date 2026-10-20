import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { Plus, UserRound } from "lucide-react"

import { BrandModelsService } from "@/client"
import { NoBrand } from "@/components/Common/NoBrand"
import { QueryError } from "@/components/Common/QueryError"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { useBrand } from "@/hooks/useBrand"
import { pageTitle, useI18n } from "@/i18n"

export const Route = createFileRoute("/_layout/models/")({
  component: ModelsPage,
  head: () => ({
    meta: [
      {
        title: pageTitle(
          "Brand Models - Jewelry Brand Studio",
          "مدل‌های برند - استودیوی برند جواهرات",
        ),
      },
    ],
  }),
})

function ModelsPage() {
  const { brand } = useBrand()
  const { t, formatDate } = useI18n()
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["models", brand?.id],
    queryFn: async () =>
      (
        await BrandModelsService.readModels({
          path: { brand_id: brand?.id ?? "" },
        })
      ).data,
    enabled: Boolean(brand),
  })

  if (!brand) return <NoBrand />
  if (isError) return <QueryError onRetry={() => refetch()} />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{t("Brand models")}</h1>
          <p className="text-sm text-muted-foreground">
            {t("Real or virtual people who wear the jewelry.")}
          </p>
        </div>
        <Button asChild>
          <Link to="/models/new">
            <Plus className="mr-2 h-4 w-4" /> {t("New model")}
          </Link>
        </Button>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">
          {t("Loading models...")}
        </p>
      ) : !data?.data.length ? (
        <div className="rounded-lg border border-dashed p-8">
          <p className="text-sm text-muted-foreground">
            {t(
              "No models yet. Create a virtual model or add a real model with consent.",
            )}
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.data.map((model) => (
            <Link key={model.id} to="/models/$id" params={{ id: model.id }}>
              <Card className="h-full transition-colors hover:border-primary/40">
                <CardHeader>
                  <div className="flex items-center justify-between gap-2">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <UserRound className="h-4 w-4" />
                      {model.name}
                    </CardTitle>
                    {model.is_default ? <Badge>{t("Default")}</Badge> : null}
                  </div>
                  <CardDescription className="capitalize">
                    {t(model.type)} · {t(model.status)}
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-xs text-muted-foreground">
                  {t("Updated {date}", {
                    date: formatDate(model.updated_at),
                  })}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
