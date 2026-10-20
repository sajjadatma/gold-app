import { useMutation } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"

import { type ProductCategory, ProductsService } from "@/client"
import { NoBrand } from "@/components/Common/NoBrand"
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

export const Route = createFileRoute("/_layout/products/new")({
  component: NewProductPage,
  head: () => ({
    meta: [
      {
        title: pageTitle(
          "New Product - Jewelry Brand Studio",
          "محصول جدید - استودیوی برند جواهرات",
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

function NewProductPage() {
  const { brand } = useBrand()
  const navigate = useNavigate()
  const { showErrorToast } = useCustomToast()
  const { t } = useI18n()
  const [form, setForm] = useState({
    name: "",
    category: "ring" as ProductCategory,
    sku: "",
    metal_type: "",
    metal_color: "",
    stone_type: "",
    description: "",
  })

  const mutation = useMutation({
    mutationFn: async () => {
      if (!brand) throw new Error(t("No brand selected"))
      return (
        await ProductsService.createProduct({
          path: { brand_id: brand.id },
          body: {
            name: form.name,
            category: form.category,
            sku: form.sku || null,
            metal_type: form.metal_type || null,
            metal_color: form.metal_color || null,
            stone_type: form.stone_type || null,
            description: form.description || null,
          },
        })
      ).data
    },
    onSuccess: (product) => {
      navigate({ to: "/products/$id", params: { id: product.id } })
    },
    onError: handleError.bind(showErrorToast),
  })

  if (!brand) return <NoBrand />

  const text = (key: keyof typeof form, label: string, placeholder = "") => (
    <div className="grid gap-2">
      <Label htmlFor={key}>{label}</Label>
      <Input
        id={key}
        value={form[key] as string}
        placeholder={placeholder}
        onChange={(event) => setForm({ ...form, [key]: event.target.value })}
      />
    </div>
  )

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{t("New product")}</h1>
        <p className="text-sm text-muted-foreground">
          {t(
            "Add the piece's details. Source photos can be uploaded on the next screen.",
          )}
        </p>
      </div>

      <form
        onSubmit={(event) => {
          event.preventDefault()
          if (form.name.trim()) mutation.mutate()
        }}
      >
        <Card>
          <CardHeader>
            <CardTitle>{t("Product details")}</CardTitle>
            <CardDescription>
              {t("Only name and category are required.")}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="grid gap-2">
              <Label htmlFor="product-name">{t("Name")}</Label>
              <Input
                id="product-name"
                value={form.name}
                onChange={(event) =>
                  setForm({ ...form, name: event.target.value })
                }
                placeholder={t("e.g. Solitaire Ring")}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="product-category">{t("Category")}</Label>
              <Select
                value={form.category}
                onValueChange={(value) =>
                  setForm({ ...form, category: value as ProductCategory })
                }
              >
                <SelectTrigger id="product-category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((category) => (
                    <SelectItem
                      key={category}
                      value={category}
                      className="capitalize"
                    >
                      {t(category)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {text("sku", t("SKU (optional)"))}
            {text("metal_type", t("Metal type"), t("e.g. 18k gold"))}
            {text("metal_color", t("Metal color"), t("e.g. yellow gold"))}
            {text("stone_type", t("Stone type"), t("e.g. diamond"))}
            <div className="grid gap-2 md:col-span-2">
              <Label htmlFor="product-description">{t("Description")}</Label>
              <Textarea
                id="product-description"
                rows={3}
                value={form.description}
                onChange={(event) =>
                  setForm({ ...form, description: event.target.value })
                }
              />
            </div>
            <div className="md:col-span-2">
              <Button
                type="submit"
                disabled={!form.name.trim() || mutation.isPending}
              >
                {mutation.isPending ? t("Creating...") : t("Create product")}
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  )
}
