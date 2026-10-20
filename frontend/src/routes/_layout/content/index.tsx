import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { FileText } from "lucide-react"

import { ContentService, ProductsService } from "@/client"
import { NoBrand } from "@/components/Common/NoBrand"
import { QueryError } from "@/components/Common/QueryError"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useBrand } from "@/hooks/useBrand"
import { pageTitle, useI18n } from "@/i18n"

export const Route = createFileRoute("/_layout/content/")({
  component: ContentPage,
  head: () => ({
    meta: [
      {
        title: pageTitle(
          "Content - Jewelry Brand Studio",
          "محتوا - استودیوی برند جواهرات",
        ),
      },
    ],
  }),
})

const statusVariant = (status: string) => {
  if (status === "approved" || status === "published") return "default" as const
  if (status === "rejected" || status === "publish_failed")
    return "destructive" as const
  return "secondary" as const
}

function ContentPage() {
  const { brand } = useBrand()
  const { t, formatDate } = useI18n()
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["drafts", brand?.id],
    queryFn: async () =>
      (
        await ContentService.readDrafts({
          path: { brand_id: brand?.id ?? "" },
        })
      ).data,
    enabled: Boolean(brand),
  })

  const { data: products } = useQuery({
    queryKey: ["products", brand?.id],
    queryFn: async () =>
      (
        await ProductsService.readProducts({
          path: { brand_id: brand?.id ?? "" },
          query: {},
        })
      ).data,
    enabled: Boolean(brand),
  })

  if (!brand) return <NoBrand />
  if (isError) return <QueryError onRetry={() => refetch()} />
  const productNames = new Map(
    (products?.data ?? []).map((product) => [product.id, product.name]),
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{t("Content")}</h1>
        <p className="text-sm text-muted-foreground">
          {t("Drafts, approvals, and published posts.")}
        </p>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">
          {t("Loading content...")}
        </p>
      ) : !data?.data.length ? (
        <div className="rounded-lg border border-dashed p-8 text-sm text-muted-foreground">
          {t(
            "No content drafts yet. Generate an image in Studio, then create a draft from it.",
          )}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {data.data.map((draft) => (
            <Link key={draft.id} to="/content/$id" params={{ id: draft.id }}>
              <Card className="h-full transition-colors hover:border-primary/40">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between gap-2 text-base">
                    <span className="flex min-w-0 items-center gap-2">
                      <FileText className="h-4 w-4 shrink-0" />
                      <span className="truncate">
                        {productNames.get(draft.product_id) ??
                          t("Content draft")}
                      </span>
                    </span>
                    <Badge
                      variant={statusVariant(draft.status)}
                      className="capitalize"
                    >
                      {t(draft.status)}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-1 text-sm text-muted-foreground">
                  <p className="line-clamp-2">
                    {draft.caption || t("No caption yet.")}
                  </p>
                  <p className="text-xs">
                    {t("Updated {date}", {
                      date: formatDate(draft.updated_at, {
                        dateStyle: "medium",
                        timeStyle: "short",
                      }),
                    })}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
