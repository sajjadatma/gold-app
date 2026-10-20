import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft, RefreshCw } from "lucide-react"
import { useEffect, useState } from "react"

import { GenerationsService, ProductsService } from "@/client"
import { NoBrand } from "@/components/Common/NoBrand"
import { ProductImage } from "@/components/Products/ProductImage"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useBrand } from "@/hooks/useBrand"
import useCustomToast from "@/hooks/useCustomToast"
import { fetchPrivateFile } from "@/lib/privateFiles"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/studio/generations/$id")({
  component: GenerationDetailPage,
  head: () => ({ meta: [{ title: "Generation - Jewelry Brand Studio" }] }),
})

function GeneratedImage({
  brandId,
  assetId,
}: {
  brandId: string
  assetId: string
}) {
  const [url, setUrl] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    let objectUrl: string | null = null
    fetchPrivateFile(
      `/api/v1/brands/${brandId}/generations/assets/${assetId}/download`,
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
  }, [brandId, assetId])

  if (!url) return <Skeleton className="h-full w-full" />
  return (
    <img
      src={url}
      alt="Generated jewelry"
      className="h-full w-full object-contain"
    />
  )
}

function GenerationDetailPage() {
  const { id } = Route.useParams()
  const { brand } = useBrand()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()

  const { data, isLoading } = useQuery({
    queryKey: ["generation", brand?.id, id],
    queryFn: async () =>
      (
        await GenerationsService.readGeneration({
          path: { brand_id: brand?.id ?? "", request_id: id },
        })
      ).data,
    enabled: Boolean(brand),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === "queued" || status === "processing" ? 2000 : false
    },
  })

  const { data: product } = useQuery({
    queryKey: ["product", brand?.id, data?.product_id],
    queryFn: async () =>
      (
        await ProductsService.readProduct({
          path: {
            brand_id: brand?.id ?? "",
            product_id: data?.product_id ?? "",
          },
        })
      ).data,
    enabled: Boolean(brand && data),
  })

  const retry = useMutation({
    mutationFn: async () =>
      GenerationsService.retryGeneration({
        path: { brand_id: brand?.id ?? "", request_id: id },
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["generation", brand?.id, id],
      })
      showSuccessToast("Generation restarted")
    },
    onError: handleError.bind(showErrorToast),
  })

  if (!brand) return <NoBrand />
  if (isLoading)
    return (
      <p className="text-sm text-muted-foreground">Loading generation...</p>
    )
  if (!data)
    return (
      <p className="text-sm text-muted-foreground">Generation not found.</p>
    )

  const sourceImage =
    product?.images.find((image) => image.is_primary) ?? product?.images[0]
  const asset = data.assets[0]

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" asChild className="-ml-2">
        <Link to="/studio">
          <ArrowLeft className="mr-2 h-4 w-4" /> Studio
        </Link>
      </Button>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold capitalize">
            {data.mode.replace("_", " ")} generation
          </h1>
          <p className="text-sm text-muted-foreground">
            {product?.name ?? "Product"} · {data.aspect_ratio} ·{" "}
            {new Date(data.created_at).toLocaleString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant={
              data.status === "completed"
                ? "default"
                : data.status === "failed"
                  ? "destructive"
                  : "secondary"
            }
            className="capitalize"
          >
            {data.status}
          </Badge>
          {data.status === "failed" ? (
            <Button variant="outline" onClick={() => retry.mutate()}>
              <RefreshCw className="mr-2 h-4 w-4" /> Retry
            </Button>
          ) : null}
        </div>
      </div>

      {data.error_message ? (
        <p className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
          {data.error_message}
        </p>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Source</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="aspect-square overflow-hidden rounded-md bg-muted">
              {sourceImage ? (
                <ProductImage
                  brandId={brand.id}
                  productId={data.product_id}
                  imageId={sourceImage.id}
                  className="h-full w-full object-contain"
                />
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  Source image unavailable
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Generated result</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="aspect-square overflow-hidden rounded-md bg-muted">
              {asset ? (
                <GeneratedImage brandId={brand.id} assetId={asset.id} />
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  {data.status === "failed" ? "No result" : "Processing..."}
                </div>
              )}
            </div>
            {asset ? (
              <div className="mt-3 flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Integrity</span>
                <Badge variant="outline" className="capitalize">
                  {asset.integrity_status.replace("_", " ")}
                </Badge>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <details className="rounded-lg border p-4 text-sm">
        <summary className="cursor-pointer font-medium">
          Request details
        </summary>
        <dl className="mt-3 grid gap-2 text-muted-foreground sm:grid-cols-2">
          <div>Provider: {data.provider}</div>
          <div>Model: {data.model ?? "—"}</div>
          <div>Prompt version: {data.prompt_version}</div>
          <div>Status: {data.status}</div>
        </dl>
      </details>
    </div>
  )
}
