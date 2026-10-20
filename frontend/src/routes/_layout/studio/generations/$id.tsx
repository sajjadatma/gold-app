import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { ArrowLeft, FileText, RefreshCw } from "lucide-react"

import { ContentService, GenerationsService, ProductsService } from "@/client"
import { NoBrand } from "@/components/Common/NoBrand"
import { GeneratedImage } from "@/components/Generations/GeneratedImage"
import { ProductImage } from "@/components/Products/ProductImage"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useBrand } from "@/hooks/useBrand"
import useCustomToast from "@/hooks/useCustomToast"
import { pageTitle, useI18n } from "@/i18n"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/studio/generations/$id")({
  component: GenerationDetailPage,
  head: () => ({
    meta: [
      {
        title: pageTitle(
          "Generation - Jewelry Brand Studio",
          "تولید - استودیوی برند جواهرات",
        ),
      },
    ],
  }),
})

function GenerationDetailPage() {
  const { id } = Route.useParams()
  const { brand } = useBrand()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const { t, formatDate } = useI18n()

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

  const createDraft = useMutation({
    mutationFn: async (assetId: string) =>
      ContentService.createDraft({
        path: { brand_id: brand?.id ?? "" },
        body: { generated_asset_id: assetId },
      }),
    onSuccess: (response) => {
      navigate({ to: "/content/$id", params: { id: response.data.id } })
    },
    onError: handleError.bind(showErrorToast),
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
      showSuccessToast(t("Generation restarted"))
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
          <ArrowLeft className="mr-2 h-4 w-4" /> {t("Studio")}
        </Link>
      </Button>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold capitalize">{t(data.mode)}</h1>
          <p className="text-sm text-muted-foreground">
            {product?.name ?? t("Product")} · {data.aspect_ratio} ·{" "}
            {formatDate(data.created_at, {
              dateStyle: "medium",
              timeStyle: "short",
            })}
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
            {t(data.status)}
          </Badge>
          {data.status === "failed" ? (
            <Button variant="outline" onClick={() => retry.mutate()}>
              <RefreshCw className="mr-2 h-4 w-4" /> {t("Retry")}
            </Button>
          ) : null}
          {asset ? (
            <Button
              onClick={() => createDraft.mutate(asset.id)}
              disabled={createDraft.isPending}
            >
              <FileText className="mr-2 h-4 w-4" /> {t("Create content draft")}
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
            <CardTitle>{t("Source")}</CardTitle>
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
                  {t("Source image unavailable")}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("Generated result")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="aspect-square overflow-hidden rounded-md bg-muted">
              {asset ? (
                <GeneratedImage brandId={brand.id} assetId={asset.id} />
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  {data.status === "failed"
                    ? t("No result")
                    : t("Processing...")}
                </div>
              )}
            </div>
            {asset ? (
              <div className="mt-3 space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">
                    {t("Integrity")}
                  </span>
                  <Badge
                    variant={
                      asset.integrity_status === "failed"
                        ? "destructive"
                        : "outline"
                    }
                    className="capitalize"
                  >
                    {t(asset.integrity_status)}
                  </Badge>
                </div>
                {typeof asset.integrity_findings_json.summary === "string" ? (
                  <p className="text-muted-foreground">
                    {asset.integrity_findings_json.summary}
                  </p>
                ) : null}
                {Array.isArray(asset.integrity_findings_json.checks) ? (
                  <ul className="list-disc pl-5 text-xs text-muted-foreground">
                    {(
                      asset.integrity_findings_json.checks as Array<
                        Record<string, unknown>
                      >
                    ).map((check, index) => (
                      <li key={index}>
                        {String(check.name)}: {String(check.result)}
                        {check.note ? ` — ${String(check.note)}` : ""}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <details className="rounded-lg border p-4 text-sm">
        <summary className="cursor-pointer font-medium">
          {t("Request details")}
        </summary>
        <dl className="mt-3 grid gap-2 text-muted-foreground sm:grid-cols-2">
          <div>
            {t("Provider")}: {data.provider}
          </div>
          <div>
            {t("Model")}: {data.model ?? "—"}
          </div>
          <div>
            {t("Prompt version")}: {data.prompt_version}
          </div>
          <div>
            {t("Status")}: {t(data.status)}
          </div>
        </dl>
      </details>
    </div>
  )
}
