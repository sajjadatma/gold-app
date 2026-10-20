import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft, Download } from "lucide-react"

import { BrandImportService } from "@/client"
import { AssetThumb } from "@/components/Assets/AssetThumb"
import { NoBrand } from "@/components/Common/NoBrand"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useBrand } from "@/hooks/useBrand"
import { downloadPrivateFile } from "@/lib/privateFiles"

export const Route = createFileRoute("/_layout/brand/imports/$id")({
  component: ImportDetailPage,
  head: () => ({ meta: [{ title: "Import Detail - Jewelry Brand Studio" }] }),
})

function ImportDetailPage() {
  const { id } = Route.useParams()
  const { brand } = useBrand()

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

  if (!brand) return <NoBrand />
  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading import...</p>
  }
  if (!data) {
    return <p className="text-sm text-muted-foreground">Import not found.</p>
  }

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" asChild className="-ml-2">
        <Link to="/brand/import">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to import
        </Link>
      </Button>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Import detail</h1>
          <p className="text-sm text-muted-foreground">
            {data.processed_file_count} processed · {data.error_count} errors
          </p>
        </div>
        <Badge
          variant={data.status === "completed" ? "default" : "secondary"}
          className="capitalize"
        >
          {data.status.replace("_", " ")}
        </Badge>
      </div>

      {data.assets.length === 0 ? (
        <p className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
          No files were stored from this import.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.assets.map((asset) => (
            <div key={asset.id} className="overflow-hidden rounded-lg border">
              <div className="aspect-[4/3] bg-muted">
                <AssetThumb brandId={brand.id} asset={asset} />
              </div>
              <div className="space-y-2 p-3">
                <p className="truncate text-sm font-medium" title={asset.original_filename}>
                  {asset.original_filename}
                </p>
                <div className="flex items-center justify-between gap-2">
                  <Badge variant="outline" className="capitalize">
                    {asset.asset_type.replace("_", " ")}
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
