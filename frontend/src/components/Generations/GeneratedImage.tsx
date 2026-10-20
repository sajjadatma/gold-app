import { useEffect, useState } from "react"

import { Skeleton } from "@/components/ui/skeleton"
import { fetchPrivateFile } from "@/lib/privateFiles"

export function GeneratedImage({
  brandId,
  assetId,
  className = "h-full w-full object-contain",
  alt = "Generated jewelry",
}: {
  brandId: string
  assetId: string
  className?: string
  alt?: string
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
  return <img src={url} alt={alt} className={className} />
}
