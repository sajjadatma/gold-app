import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { ArrowLeft, Download, Sparkles } from "lucide-react"

import { BrandImportService } from "@/client"
import { AssetThumb } from "@/components/Assets/AssetThumb"
import { NoBrand } from "@/components/Common/NoBrand"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useBrand } from "@/hooks/useBrand"
import useCustomToast from "@/hooks/useCustomToast"
import { pageTitle, useI18n } from "@/i18n"
import { downloadPrivateFile } from "@/lib/privateFiles"

export const Route = createFileRoute("/_layout/brand/imports/$id")({
  component: ImportDetailPage,
  head: () => ({
    meta: [
      {
        title: pageTitle(
          "Import Detail - Jewelry Brand Studio",
          "جزئیات ورود - استودیوی برند جواهرات",
        ),
      },
    ],
  }),
})

function ImportDetailPage() {
  const { id } = Route.useParams()
  const { brand } = useBrand()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const { t } = useI18n()

  const { data, isLoading } = useQuery({
    queryKey: ["import", brand?.id, id],
    queryFn: async () =>
      (
        await BrandImportService.readImport({
          path: { brand_id: brand?.id ?? "", import_id: id },
        })
      ).data,
    enabled: Boolean(brand),
  })

  const analyze = useMutation({
    mutationFn: async () =>
      (
        await BrandImportService.analyzeImportEndpoint({
          path: { brand_id: brand?.id ?? "", import_id: id },
        })
      ).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["profile", brand?.id] })
      showSuccessToast(t("Brand profile ready for review"))
      navigate({ to: "/brand/profile" })
    },
    onError: () => showErrorToast(t("Brand analysis failed. Please retry.")),
  })

  if (!brand) return <NoBrand />
  if (isLoading) {
    return <p className="text-sm text-muted-foreground">{t("Loading...")}</p>
  }
  if (!data) {
    return (
      <p className="text-sm text-muted-foreground">{t("Import not found")}</p>
    )
  }

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" asChild className="-ml-2">
        <Link to="/brand/import">
          <ArrowLeft className="mr-2 h-4 w-4" /> {t("Back to import")}
        </Link>
      </Button>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{t("Import detail")}</h1>
          <p className="text-sm text-muted-foreground">
            {t("{count} processed · {errors} errors", {
              count: data.processed_file_count,
              errors: data.error_count,
            })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant={data.status === "completed" ? "default" : "secondary"}
            className="capitalize"
          >
            {t(data.status)}
          </Badge>
          <Button
            onClick={() => analyze.mutate()}
            disabled={analyze.isPending || data.assets.length === 0}
          >
            <Sparkles className="mr-2 h-4 w-4" />
            {analyze.isPending ? t("Analyzing") : t("Analyze brand")}
          </Button>
        </div>
      </div>

      {data.assets.length === 0 ? (
        <p className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
          {t("No files were stored from this import.")}
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.assets.map((asset) => (
            <div key={asset.id} className="overflow-hidden rounded-lg border">
              <div className="aspect-[4/3] bg-muted">
                <AssetThumb brandId={brand.id} asset={asset} />
              </div>
              <div className="space-y-2 p-3">
                <p
                  className="truncate text-sm font-medium"
                  title={asset.original_filename}
                >
                  {asset.original_filename}
                </p>
                <div className="flex items-center justify-between gap-2">
                  <Badge variant="outline" className="capitalize">
                    {t(asset.asset_type.replace(/_/g, " "))}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      downloadPrivateFile(
                        `/api/v1/brands/${brand.id}/assets/${asset.id}/download`,
                        asset.original_filename,
                      )
                    }
                  >
                    <Download className="h-4 w-4" />
                    <span className="sr-only">Download</span>
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
