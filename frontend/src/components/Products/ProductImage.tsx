import { useEffect, useState } from "react"

import { Skeleton } from "@/components/ui/skeleton"
import { fetchPrivateFile } from "@/lib/privateFiles"

export function ProductImage({
  brandId,
  productId,
  imageId,
  alt = "Product source",
  className = "h-full w-full object-cover",
}: {
  brandId: string
  productId: string
  imageId: string
  alt?: string
  className?: string
}) {
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
  return <img src={url} alt={alt} className={className} />
}
