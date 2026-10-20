import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { Gem, Plus } from "lucide-react"
import { useEffect, useState } from "react"

import { ProductsService } from "@/client"
import { NoBrand } from "@/components/Common/NoBrand"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useBrand } from "@/hooks/useBrand"
import { pageTitle, useI18n } from "@/i18n"
import { fetchPrivateFile } from "@/lib/privateFiles"

export const Route = createFileRoute("/_layout/products/")({
  component: ProductsPage,
  head: () => ({
    meta: [
      {
        title: pageTitle(
          "Products - Jewelry Brand Studio",
          "محصولات - استودیوی برند جواهرات",
        ),
      },
    ],
  }),
})

function ProductThumb({
  brandId,
  productId,
  imageId,
}: {
  brandId: string
  productId: string
  imageId: string
}) {
  const { t } = useI18n()
  const [url, setUrl] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    let objectUrl: string | null = null
    fetchPrivateFile(
      `/api/v1/brands/${brandId}/products/${productId}/images/${imageId}/download`,
    )
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob)
        if (active) setUrl(objectUrl)
      })
      .catch(() => undefined)
    return () => {
      active = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [brandId, productId, imageId])

  if (!url) return <Skeleton className="h-full w-full" />
  return (
    <img
      src={url}
      alt={t("Product source")}
      className="h-full w-full object-cover"
    />
  )
}

function ProductsPage() {
  const { brand } = useBrand()
  const { t } = useI18n()
  const { data, isLoading } = useQuery({
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{t("Products")}</h1>
          <p className="text-sm text-muted-foreground">
            {t("Jewelry pieces available for photography.")}
          </p>
        </div>
        <Button asChild>
          <Link to="/products/new">
            <Plus className="mr-2 h-4 w-4" /> {t("New product")}
          </Link>
        </Button>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">
          {t("Loading products...")}
        </p>
      ) : !data?.data.length ? (
        <div className="rounded-lg border border-dashed p-8">
          <p className="text-sm text-muted-foreground">
            {t(
              "No products yet. Add a jewelry piece and at least one source photo.",
            )}
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.data.map((product) => {
            const primary =
              product.images.find((image) => image.is_primary) ??
              product.images[0]
            return (
              <Link
                key={product.id}
                to="/products/$id"
                params={{ id: product.id }}
              >
                <Card className="h-full overflow-hidden transition-colors hover:border-primary/40">
                  <div className="aspect-square bg-muted">
                    {primary ? (
                      <ProductThumb
                        brandId={brand.id}
                        productId={product.id}
                        imageId={primary.id}
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center">
                        <Gem className="h-10 w-10 text-muted-foreground" />
                      </div>
                    )}
                  </div>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between gap-2 text-base">
                      <span className="truncate">{product.name}</span>
                      <Badge variant="outline" className="capitalize">
                        {t(product.category)}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-xs text-muted-foreground">
                    {t(
                      product.images.length === 1
                        ? "{count} source image"
                        : "{count} source images",
                      { count: product.images.length },
                    )}
                  </CardContent>
                </Card>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
