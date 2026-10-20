import { FileText, ImageOff } from "lucide-react"
import { useEffect, useState } from "react"

import type { BrandAssetPublic } from "@/client"
import { Skeleton } from "@/components/ui/skeleton"
import { fetchPrivateFile } from "@/lib/privateFiles"

export function AssetThumb({
  brandId,
  asset,
  className = "h-full w-full object-cover",
}: {
  brandId: string
  asset: BrandAssetPublic
  className?: string
}) {
  const [url, setUrl] = useState<string | null>(null)
  const [failed, setFailed] = useState(false)
  const isImage = asset.content_type.startsWith("image/")
  const isPdf = asset.content_type === "application/pdf"

  useEffect(() => {
    if (!isImage) return
    let active = true
    let objectUrl: string | null = null
    fetchPrivateFile(
      `/api/v1/brands/${brandId}/assets/${asset.id}/preview`,
    )
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob)
        if (active) setUrl(objectUrl)
      })
      .catch(() => {
        if (active) setFailed(true)
      })
    return () => {
      active = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [brandId, asset.id, isImage])

  if (isPdf) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-muted">
        <FileText className="h-8 w-8 text-muted-foreground" />
      </div>
    )
  }

  if (!isImage || failed) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-muted">
        <ImageOff className="h-8 w-8 text-muted-foreground" />
      </div>
    )
  }

  if (!url) {
    return <Skeleton className="h-full w-full" />
  }

  return <img src={url} alt={asset.original_filename} className={className} />
}
