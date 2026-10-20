import { useMutation, useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { Camera } from "lucide-react"
import { useState } from "react"

import {
  BrandModelsService,
  type GenerationCreate,
  GenerationsService,
  ProductsService,
} from "@/client"
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
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/studio/")({
  component: StudioPage,
  head: () => ({ meta: [{ title: "Studio - Jewelry Brand Studio" }] }),
})

function StudioPage() {
  const { brand } = useBrand()
  const navigate = useNavigate()
  const { showErrorToast } = useCustomToast()
  const [productId, setProductId] = useState("")
  const [mode, setMode] = useState<GenerationCreate["mode"]>("studio")
  const [aspectRatio, setAspectRatio] =
    useState<GenerationCreate["aspect_ratio"]>("4:5")
  const [modelId, setModelId] = useState("")
  const [notes, setNotes] = useState("")

  const { data: products } = useQuery({
    queryKey: ["products", brand?.id],
    queryFn: async () =>
      (
        await ProductsService.readProducts({
          path: { brand_id: brand?.id ?? "" },
          query: {},
        })
      ).data,
    enabled: Boolean(brand),
  })

  const { data: models } = useQuery({
    queryKey: ["models", brand?.id],
    queryFn: async () =>
      (
        await BrandModelsService.readModels({
          path: { brand_id: brand?.id ?? "" },
        })
      ).data,
    enabled: Boolean(brand),
  })

  const { data: generations } = useQuery({
    queryKey: ["generations", brand?.id],
    queryFn: async () =>
      (
        await GenerationsService.readGenerations({
          path: { brand_id: brand?.id ?? "" },
        })
      ).data,
    enabled: Boolean(brand),
    refetchInterval: 3000,
  })

  const create = useMutation({
    mutationFn: async () => {
      if (!brand) throw new Error("No brand selected")
      return (
        await GenerationsService.createGeneration({
          path: { brand_id: brand.id },
          body: {
            product_id: productId,
            mode,
            aspect_ratio: aspectRatio,
            brand_model_id: modelId || null,
            style_notes: notes,
          },
        })
      ).data
    },
    onSuccess: (generation) => {
      navigate({
        to: "/studio/generations/$id",
        params: { id: generation.id },
      })
    },
    onError: handleError.bind(showErrorToast),
  })

  if (!brand) return <NoBrand />

  const readyModels = (models?.data ?? []).filter(
    (model) => model.status === "ready",
  )

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">AI photography studio</h1>
        <p className="text-sm text-muted-foreground">
          Generate branded jewelry imagery with the active brand profile.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>New generation</CardTitle>
            <CardDescription>
              Source fidelity is prioritized over creative changes.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="product">Product</Label>
              <Select value={productId} onValueChange={setProductId}>
                <SelectTrigger id="product">
                  <SelectValue placeholder="Select a product" />
                </SelectTrigger>
                <SelectContent>
                  {(products?.data ?? []).map((product) => (
                    <SelectItem key={product.id} value={product.id}>
                      {product.name} ({product.images.length} image
                      {product.images.length === 1 ? "" : "s"})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="mode">Mode</Label>
                <Select
                  value={mode}
                  onValueChange={(value) =>
                    setMode(value as GenerationCreate["mode"])
                  }
                >
                  <SelectTrigger id="mode">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="studio">Studio</SelectItem>
                    <SelectItem value="on_model">On model</SelectItem>
                    <SelectItem value="campaign">Campaign</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="ratio">Aspect ratio</Label>
                <Select
                  value={aspectRatio}
                  onValueChange={(value) =>
                    setAspectRatio(value as GenerationCreate["aspect_ratio"])
                  }
                >
                  <SelectTrigger id="ratio">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1:1">1:1 feed</SelectItem>
                    <SelectItem value="4:5">4:5 portrait</SelectItem>
                    <SelectItem value="9:16">9:16 story</SelectItem>
                    <SelectItem value="16:9">16:9 landscape</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {mode === "on_model" ? (
              <div className="grid gap-2">
                <Label htmlFor="model">Brand model</Label>
                <Select value={modelId} onValueChange={setModelId}>
                  <SelectTrigger id="model">
                    <SelectValue placeholder="Select a ready model" />
                  </SelectTrigger>
                  <SelectContent>
                    {readyModels.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        {model.name} ({model.type})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {readyModels.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    No ready models. Create and prepare a model first.
                  </p>
                ) : null}
              </div>
            ) : null}

            <div className="grid gap-2">
              <Label htmlFor="notes">Style notes (optional)</Label>
              <Textarea
                id="notes"
                rows={2}
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="e.g. keep the background warm ivory"
              />
            </div>

            <Button
              onClick={() => create.mutate()}
              disabled={
                !productId ||
                create.isPending ||
                (mode === "on_model" && !modelId)
              }
            >
              <Camera className="mr-2 h-4 w-4" />
              {create.isPending ? "Generating..." : "Generate image"}
            </Button>
          </CardContent>
        </Card>

        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Recent generations</h2>
          {!generations?.data.length ? (
            <p className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
              No generations yet.
            </p>
          ) : (
            <div className="divide-y rounded-lg border">
              {generations.data.slice(0, 8).map((generation) => (
                <Link
                  key={generation.id}
                  to="/studio/generations/$id"
                  params={{ id: generation.id }}
                  className="flex items-center justify-between gap-3 p-3 hover:bg-muted/50"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium capitalize">
                      {generation.mode.replace("_", " ")} ·{" "}
                      {generation.aspect_ratio}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(generation.created_at).toLocaleString()}
                    </p>
                  </div>
                  <Badge
                    variant={
                      generation.status === "completed"
                        ? "default"
                        : generation.status === "failed"
                          ? "destructive"
                          : "secondary"
                    }
                    className="capitalize"
                  >
                    {generation.status}
                  </Badge>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
