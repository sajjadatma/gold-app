import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { Archive, ArrowLeft, Upload } from "lucide-react"
import { useEffect, useState } from "react"

import { type ProductCategory, ProductsService } from "@/client"
import { NoBrand } from "@/components/Common/NoBrand"
import { ProductImage } from "@/components/Products/ProductImage"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useBrand } from "@/hooks/useBrand"
import useCustomToast from "@/hooks/useCustomToast"
import { pageTitle, useI18n } from "@/i18n"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/products/$id")({
  component: ProductDetailPage,
  head: () => ({
    meta: [
      {
        title: pageTitle(
          "Product - Jewelry Brand Studio",
          "محصول - استودیوی برند جواهرات",
        ),
      },
    ],
  }),
})

const categories: ProductCategory[] = [
  "ring",
  "necklace",
  "bracelet",
  "earrings",
  "set",
  "pendant",
  "other",
]

function ProductDetailPage() {
  const { id } = Route.useParams()
  const { brand } = useBrand()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const { t } = useI18n()
  const [file, setFile] = useState<File | null>(null)
  const [form, setForm] = useState({
    name: "",
    category: "ring" as ProductCategory,
    sku: "",
    metal_type: "",
    metal_color: "",
    stone_type: "",
    description: "",
    integrity_notes: "",
  })

  const { data, isLoading } = useQuery({
    queryKey: ["product", brand?.id, id],
    queryFn: async () =>
      (
        await ProductsService.readProduct({
          path: { brand_id: brand?.id ?? "", product_id: id },
        })
      ).data,
    enabled: Boolean(brand),
  })

  useEffect(() => {
    if (data) {
      setForm({
        name: data.name,
        category: data.category as ProductCategory,
        sku: data.sku ?? "",
        metal_type: data.metal_type ?? "",
        metal_color: data.metal_color ?? "",
        stone_type: data.stone_type ?? "",
        description: data.description ?? "",
        integrity_notes: data.integrity_notes ?? "",
      })
    }
  }, [data])

  const refresh = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["product", brand?.id, id],
    })
    await queryClient.invalidateQueries({ queryKey: ["products", brand?.id] })
  }

  const save = useMutation({
    mutationFn: async () =>
      ProductsService.updateProduct({
        path: { brand_id: brand?.id ?? "", product_id: id },
        body: {
          name: form.name,
          category: form.category,
          sku: form.sku || null,
          metal_type: form.metal_type || null,
          metal_color: form.metal_color || null,
          stone_type: form.stone_type || null,
          description: form.description || null,
          integrity_notes: form.integrity_notes || null,
        },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast(t("Product saved"))
    },
    onError: handleError.bind(showErrorToast),
  })

  const upload = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error(t("Choose an image first"))
      return ProductsService.uploadProductImage({
        path: { brand_id: brand?.id ?? "", product_id: id },
        body: { file },
      })
    },
    onSuccess: async () => {
      setFile(null)
      await refresh()
      showSuccessToast(t("Source image uploaded"))
    },
    onError: handleError.bind(showErrorToast),
  })

  const setPrimary = useMutation({
    mutationFn: async (imageId: string) =>
      ProductsService.setPrimaryImage({
        path: { brand_id: brand?.id ?? "", product_id: id, image_id: imageId },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast(t("Primary image updated"))
    },
    onError: handleError.bind(showErrorToast),
  })

  const archive = useMutation({
    mutationFn: async () =>
      ProductsService.archiveProduct({
        path: { brand_id: brand?.id ?? "", product_id: id },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast(t("Product archived"))
    },
    onError: handleError.bind(showErrorToast),
  })

  if (!brand) return <NoBrand />
  if (isLoading)
    return <p className="text-sm text-muted-foreground">{t("Loading...")}</p>
  if (!data)
    return (
      <p className="text-sm text-muted-foreground">{t("Product not found.")}</p>
    )

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" asChild className="-ml-2">
        <Link to="/products">
          <ArrowLeft className="mr-2 h-4 w-4" /> {t("All products")}
        </Link>
      </Button>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{data.name}</h1>
          <div className="mt-2 flex items-center gap-2">
            <Badge variant="outline">{t(data.category)}</Badge>
            <Badge variant={data.status === "active" ? "default" : "secondary"}>
              {t(data.status)}
            </Badge>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => {
              if (window.confirm(t("Archive {name}?", { name: data.name })))
                archive.mutate()
            }}
          >
            <Archive className="mr-2 h-4 w-4" /> {t("Archive")}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>{t("Product details")}</CardTitle>
            <CardDescription>
              {t("Metadata used in generation and captions.")}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-2">
              <Label htmlFor="name">{t("Name")}</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(event) =>
                  setForm({ ...form, name: event.target.value })
                }
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="category">{t("Category")}</Label>
              <Select
                value={form.category}
                onValueChange={(value) =>
                  setForm({ ...form, category: value as ProductCategory })
                }
              >
                <SelectTrigger id="category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((category) => (
                    <SelectItem
                      key={category}
                      value={category}
                      className="capitalize"
                    >
                      {category}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="sku">{t("SKU")}</Label>
              <Input
                id="sku"
                value={form.sku}
                onChange={(event) =>
                  setForm({ ...form, sku: event.target.value })
                }
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="metal_type">{t("Metal type")}</Label>
              <Input
                id="metal_type"
                value={form.metal_type}
                onChange={(event) =>
                  setForm({ ...form, metal_type: event.target.value })
                }
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="metal_color">{t("Metal color")}</Label>
              <Input
                id="metal_color"
                value={form.metal_color}
                onChange={(event) =>
                  setForm({ ...form, metal_color: event.target.value })
                }
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="stone_type">{t("Stone type")}</Label>
              <Input
                id="stone_type"
                value={form.stone_type}
                onChange={(event) =>
                  setForm({ ...form, stone_type: event.target.value })
                }
              />
            </div>
            <div className="grid gap-2 sm:col-span-2">
              <Label htmlFor="description">{t("Description")}</Label>
              <Textarea
                id="description"
                rows={3}
                value={form.description}
                onChange={(event) =>
                  setForm({ ...form, description: event.target.value })
                }
              />
            </div>
            <div className="grid gap-2 sm:col-span-2">
              <Label htmlFor="integrity_notes">{t("Integrity notes")}</Label>
              <Textarea
                id="integrity_notes"
                rows={2}
                value={form.integrity_notes}
                onChange={(event) =>
                  setForm({ ...form, integrity_notes: event.target.value })
                }
              />
            </div>
            <div className="sm:col-span-2">
              <Button onClick={() => save.mutate()} disabled={save.isPending}>
                {save.isPending ? t("Saving...") : t("Save product")}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("Source images")}</CardTitle>
            <CardDescription>
              {t("At least one photo is required before generation.")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="source-image">{t("Add image")}</Label>
              <Input
                id="source-image"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
              <Button
                className="w-fit"
                onClick={() => upload.mutate()}
                disabled={!file || upload.isPending}
              >
                <Upload className="mr-2 h-4 w-4" />
                {upload.isPending ? t("Uploading...") : t("Upload")}
              </Button>
            </div>

            {data.images.length === 0 ? (
              <p className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
                {t("No source images yet.")}
              </p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {data.images.map((image) => (
                  <div
                    key={image.id}
                    className="overflow-hidden rounded-lg border"
                  >
                    <div className="aspect-square bg-muted">
                      <ProductImage
                        brandId={brand.id}
                        productId={data.id}
                        imageId={image.id}
                      />
                    </div>
                    <div className="space-y-2 p-2">
                      <div className="flex items-center justify-between gap-2">
                        <Badge
                          variant={
                            image.quality_status === "ok"
                              ? "outline"
                              : "secondary"
                          }
                        >
                          {t(image.quality_status)}
                        </Badge>
                        {image.is_primary ? (
                          <Badge>{t("Primary")}</Badge>
                        ) : (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setPrimary.mutate(image.id)}
                            disabled={setPrimary.isPending}
                          >
                            {t("Set primary")}
                          </Button>
                        )}
                      </div>
                      {Array.isArray(image.quality_findings_json.warnings) &&
                      image.quality_findings_json.warnings.length ? (
                        <p className="text-xs text-muted-foreground">
                          {(image.quality_findings_json.warnings as string[])
                            .map((warning) => t(warning.replace(/_/g, " ")))
                            .join("، ")}
                        </p>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
