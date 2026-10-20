import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { Upload } from "lucide-react"
import { useState } from "react"

import { type BrandImportPublic, BrandImportService } from "@/client"
import { NoBrand } from "@/components/Common/NoBrand"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useBrand } from "@/hooks/useBrand"
import useCustomToast from "@/hooks/useCustomToast"
import { uploadBrandFiles } from "@/lib/privateFiles"

export const Route = createFileRoute("/_layout/brand/import")({
  component: ImportPage,
  head: () => ({ meta: [{ title: "Brand Import - Jewelry Brand Studio" }] }),
})

const statusVariant = (status: string) => {
  if (status === "completed") return "default" as const
  if (status === "failed") return "destructive" as const
  return "secondary" as const
}

function ImportPage() {
  const { brand } = useBrand()
  const navigate = useNavigate()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)

  const { data, refetch } = useQuery({
    queryKey: ["imports", brand?.id],
    queryFn: async () =>
      (
        await BrandImportService.readImports({
          path: { brand_id: brand?.id ?? "" },
        })
      ).data,
    enabled: Boolean(brand),
  })

  if (!brand) return <NoBrand />

  const upload = async () => {
    if (!files.length) return
    setUploading(true)
    try {
      const result = (await uploadBrandFiles(brand.id, files)) as { id: string }
      showSuccessToast("Import processed")
      setFiles([])
      await refetch()
      navigate({ to: "/brand/imports/$id", params: { id: result.id } })
    } catch (error) {
      showErrorToast(error instanceof Error ? error.message : "Upload failed")
    } finally {
      setUploading(false)
    }
  }

  const imports: BrandImportPublic[] = data?.data ?? []

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Import brand assets</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Upload the brand book, logos, fonts, campaign references, patterns,
          and design sources your brand already uses. PDF, images, SVG, fonts,
          ZIP, AI, EPS, and PSD are accepted.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>New import</CardTitle>
          <CardDescription>
            Files are stored privately and validated before processing.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="brand-files">Files</Label>
            <Input
              id="brand-files"
              type="file"
              multiple
              onChange={(event) =>
                setFiles(Array.from(event.target.files ?? []))
              }
            />
            {files.length ? (
              <p className="text-xs text-muted-foreground">
                {files.length} file{files.length === 1 ? "" : "s"} selected
              </p>
            ) : null}
          </div>
          <Button onClick={upload} disabled={!files.length || uploading}>
            <Upload className="mr-2 h-4 w-4" />
            {uploading ? "Processing..." : "Upload and process"}
          </Button>
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Recent imports</h2>
        {imports.length === 0 ? (
          <p className="text-sm text-muted-foreground">No imports yet.</p>
        ) : (
          <div className="divide-y rounded-lg border">
            {imports.map((item) => (
              <Link
                key={item.id}
                to="/brand/imports/$id"
                params={{ id: item.id }}
                className="flex flex-wrap items-center justify-between gap-3 p-4 hover:bg-muted/50"
              >
                <div>
                  <p className="text-sm font-medium">
                    {new Date(item.created_at).toLocaleString()}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {item.processed_file_count} processed · {item.error_count}{" "}
                    errors
                  </p>
                </div>
                <Badge variant={statusVariant(item.status)}>
                  {item.status.replace("_", " ")}
                </Badge>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
