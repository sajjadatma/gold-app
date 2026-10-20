import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Download, Trash2 } from "lucide-react"
import { useState } from "react"

import { BrandImportService } from "@/client"
import { AssetThumb } from "@/components/Assets/AssetThumb"
import { NoBrand } from "@/components/Common/NoBrand"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useBrand } from "@/hooks/useBrand"
import useCustomToast from "@/hooks/useCustomToast"
import { downloadPrivateFile } from "@/lib/privateFiles"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/brand/assets")({
  component: AssetsPage,
  head: () => ({ meta: [{ title: "Brand Assets - Jewelry Brand Studio" }] }),
})

const assetTypes = [
  "brand_book",
  "logo",
  "font",
  "image",
  "campaign_reference",
  "pattern",
  "graphic_element",
  "design_source",
  "other",
]

function AssetsPage() {
  const { brand } = useBrand()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [filter, setFilter] = useState("all")

  const { data, isLoading } = useQuery({
    queryKey: ["assets", brand?.id, filter],
    queryFn: async () =>
      (
        await BrandImportService.readAssets({
          path: { brand_id: brand?.id ?? "" },
          query: filter === "all" ? {} : { asset_type: filter },
        })
      ).data,
    enabled: Boolean(brand),
  })

  const archive = useMutation({
    mutationFn: async (assetId: string) =>
      BrandImportService.archiveAsset({
        path: { brand_id: brand?.id ?? "", asset_id: assetId },
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["assets", brand?.id] })
      showSuccessToast("Asset removed from active use")
    },
    onError: handleError.bind(showErrorToast),
  })

  if (!brand) return <NoBrand />
  const isOwner = brand.role === "owner"

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Brand assets</h1>
          <p className="text-sm text-muted-foreground">
            Originals are preserved. Removing an asset only takes it out of
            active use.
          </p>
        </div>
        <div className="grid w-56 gap-2">
          <Label htmlFor="asset-filter">Filter by type</Label>
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger id="asset-filter">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {assetTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {type.replace("_", " ")}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading assets...</p>
      ) : !data?.data.length ? (
        <p className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
          No assets yet. Import brand material to get started.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {data.data.map((asset) => (
            <div key={asset.id} className="overflow-hidden rounded-lg border">
              <div className="aspect-square bg-muted">
                <AssetThumb brandId={brand.id} asset={asset} />
              </div>
              <div className="space-y-2 p-3">
                <p
                  className="truncate text-sm font-medium"
                  title={asset.original_filename}
                >
                  {asset.original_filename}
                </p>
                <div className="flex items-center justify-between gap-1">
                  <Badge variant="outline" className="capitalize">
                    {asset.asset_type.replace("_", " ")}
                  </Badge>
                  <div className="flex">
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label={`Download ${asset.original_filename}`}
                      onClick={() =>
                        downloadPrivateFile(
                          `/api/v1/brands/${brand.id}/assets/${asset.id}/download`,
                          asset.original_filename,
                        )
                      }
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    {isOwner ? (
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`Archive ${asset.original_filename}`}
                        onClick={() => {
                          if (
                            window.confirm(
                              `Remove ${asset.original_filename} from active use?`,
                            )
                          ) {
                            archive.mutate(asset.id)
                          }
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    ) : null}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
