import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { FileText } from "lucide-react"

import { ContentService, ProductsService } from "@/client"
import { NoBrand } from "@/components/Common/NoBrand"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useBrand } from "@/hooks/useBrand"

export const Route = createFileRoute("/_layout/content/")({
  component: ContentPage,
  head: () => ({ meta: [{ title: "Content - Jewelry Brand Studio" }] }),
})

const statusVariant = (status: string) => {
  if (status === "approved" || status === "published") return "default" as const
  if (status === "rejected" || status === "publish_failed")
    return "destructive" as const
  return "secondary" as const
}

function ContentPage() {
  const { brand } = useBrand()
  const { data, isLoading } = useQuery({
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
  const productNames = new Map(
    (products?.data ?? []).map((product) => [product.id, product.name]),
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Content</h1>
        <p className="text-sm text-muted-foreground">
          Drafts, approvals, and published posts.
        </p>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading content...</p>
      ) : !data?.data.length ? (
        <div className="rounded-lg border border-dashed p-8 text-sm text-muted-foreground">
          No content drafts yet. Generate an image in Studio, then create a
          draft from it.
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
                        {productNames.get(draft.product_id) ?? "Content draft"}
                      </span>
                    </span>
                    <Badge
                      variant={statusVariant(draft.status)}
                      className="capitalize"
                    >
                      {draft.status.replace("_", " ")}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-1 text-sm text-muted-foreground">
                  <p className="line-clamp-2">
                    {draft.caption || "No caption yet."}
                  </p>
                  <p className="text-xs">
                    Updated {new Date(draft.updated_at).toLocaleString()}
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
