import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  RefreshCw,
  Send,
  Share2,
  Sparkles,
  XCircle,
} from "lucide-react"
import { useEffect, useState } from "react"

import { ContentService, ProductsService, PublishingService } from "@/client"
import { NoBrand } from "@/components/Common/NoBrand"
import { GeneratedImage } from "@/components/Generations/GeneratedImage"
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
import { Textarea } from "@/components/ui/textarea"
import { useBrand } from "@/hooks/useBrand"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/content/$id")({
  component: ContentDetailPage,
  head: () => ({ meta: [{ title: "Content Draft - Jewelry Brand Studio" }] }),
})

function ContentDetailPage() {
  const { id } = Route.useParams()
  const { brand } = useBrand()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [caption, setCaption] = useState("")
  const [cta, setCta] = useState("")
  const [hashtags, setHashtags] = useState("")

  const { data, isLoading } = useQuery({
    queryKey: ["draft", brand?.id, id],
    queryFn: async () =>
      (
        await ContentService.readDraft({
          path: { brand_id: brand?.id ?? "", draft_id: id },
        })
      ).data,
    enabled: Boolean(brand),
  })

  const { data: product } = useQuery({
    queryKey: ["product", brand?.id, data?.product_id],
    queryFn: async () =>
      (
        await ProductsService.readProduct({
          path: {
            brand_id: brand?.id ?? "",
            product_id: data?.product_id ?? "",
          },
        })
      ).data,
    enabled: Boolean(brand && data),
  })

  const { data: publishJobs } = useQuery({
    queryKey: ["publish-jobs", brand?.id, id],
    queryFn: async () =>
      (
        await PublishingService.readPublishJobs({
          path: { brand_id: brand?.id ?? "", draft_id: id },
        })
      ).data,
    enabled: Boolean(brand && data),
  })

  useEffect(() => {
    if (data) {
      setCaption(data.caption)
      setCta(data.cta ?? "")
      setHashtags(data.hashtags)
    }
  }, [data])

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["draft", brand?.id, id] })
    await queryClient.invalidateQueries({ queryKey: ["drafts", brand?.id] })
  }

  const generate = useMutation({
    mutationFn: async (force: boolean) =>
      ContentService.generateCaptionEndpoint({
        path: { brand_id: brand?.id ?? "", draft_id: id },
        body: { force },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast("Caption generated")
    },
    onError: handleError.bind(showErrorToast),
  })

  const save = useMutation({
    mutationFn: async () =>
      ContentService.updateDraft({
        path: { brand_id: brand?.id ?? "", draft_id: id },
        body: { caption, cta, hashtags },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast("Draft saved")
    },
    onError: handleError.bind(showErrorToast),
  })

  const approve = useMutation({
    mutationFn: async () =>
      ContentService.approveDraft({
        path: { brand_id: brand?.id ?? "", draft_id: id },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast("Content approved")
    },
    onError: handleError.bind(showErrorToast),
  })

  const reject = useMutation({
    mutationFn: async () =>
      ContentService.rejectDraft({
        path: { brand_id: brand?.id ?? "", draft_id: id },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast("Content rejected")
    },
    onError: handleError.bind(showErrorToast),
  })

  const publish = useMutation({
    mutationFn: async () =>
      PublishingService.publishDraft({
        path: { brand_id: brand?.id ?? "", draft_id: id },
      }),
    onSuccess: async () => {
      await refresh()
      await queryClient.invalidateQueries({
        queryKey: ["publish-jobs", brand?.id, id],
      })
      showSuccessToast("Publish job finished")
    },
    onError: handleError.bind(showErrorToast),
  })

  const retryPublish = useMutation({
    mutationFn: async (jobId: string) =>
      PublishingService.retryPublish({
        path: { brand_id: brand?.id ?? "", job_id: jobId },
      }),
    onSuccess: async () => {
      await refresh()
      await queryClient.invalidateQueries({
        queryKey: ["publish-jobs", brand?.id, id],
      })
    },
    onError: handleError.bind(showErrorToast),
  })

  const submit = useMutation({
    mutationFn: async () =>
      ContentService.submitDraft({
        path: { brand_id: brand?.id ?? "", draft_id: id },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast("Draft submitted for approval")
    },
    onError: handleError.bind(showErrorToast),
  })

  if (!brand) return <NoBrand />
  if (isLoading)
    return <p className="text-sm text-muted-foreground">Loading draft...</p>
  if (!data)
    return <p className="text-sm text-muted-foreground">Draft not found.</p>

  const sourceImage =
    product?.images.find((image) => image.is_primary) ?? product?.images[0]
  const isEditable = !["published", "publish_failed"].includes(data.status)
  const canSubmit = ["draft", "rejected"].includes(data.status)
  const isOwner = brand.role === "owner"
  const canReview = isOwner && data.status === "needs_approval"

  return (
    <div className="space-y-6 pb-8">
      <Button variant="ghost" size="sm" asChild className="-ml-2">
        <Link to="/content">
          <ArrowLeft className="mr-2 h-4 w-4" /> All content
        </Link>
      </Button>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{data.product_name}</h1>
          <p className="text-sm text-muted-foreground">
            Profile v{data.brand_profile_version}
            {data.model_name ? ` · Model: ${data.model_name}` : ""}
            {" · "}
            {data.product_category}
          </p>
        </div>
        <Badge className="capitalize">{data.status.replace("_", " ")}</Badge>
      </div>

      {data.integrity_status === "failed" ? (
        <p className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
          Integrity failed: this output cannot be approved. Regenerate the
          image.
        </p>
      ) : data.integrity_status === "needs_review" ? (
        <p className="rounded-md border border-amber-500/40 bg-amber-500/5 p-3 text-sm">
          Integrity needs review. Compare the source and generated jewelry
          carefully before approving.
        </p>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Source jewelry</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="aspect-square overflow-hidden rounded-md bg-muted">
              {sourceImage ? (
                <ProductImage
                  brandId={brand.id}
                  productId={data.product_id}
                  imageId={sourceImage.id}
                  className="h-full w-full object-contain"
                />
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  Source unavailable
                </div>
              )}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Generated image</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="aspect-square overflow-hidden rounded-md bg-muted">
              <GeneratedImage
                brandId={brand.id}
                assetId={data.generated_asset_id}
              />
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Integrity</span>
              <Badge
                variant={
                  data.integrity_status === "failed" ? "destructive" : "outline"
                }
                className="capitalize"
              >
                {data.integrity_status.replace("_", " ")}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Social copy</CardTitle>
          <CardDescription>
            Generated from the active brand profile and product metadata.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => {
                if (data.user_edited) {
                  if (
                    window.confirm(
                      "You edited this caption manually. Regenerating will replace your text. Continue?",
                    )
                  ) {
                    generate.mutate(true)
                  }
                } else {
                  generate.mutate(false)
                }
              }}
              disabled={generate.isPending || !isEditable}
            >
              <Sparkles className="mr-2 h-4 w-4" />
              {generate.isPending ? "Generating..." : "Generate caption"}
            </Button>
            {data.user_edited ? (
              <Badge variant="outline">Manually edited</Badge>
            ) : null}
          </div>

          {data.alternative_captions_json.length ? (
            <div className="space-y-2">
              <Label>Alternatives</Label>
              {data.alternative_captions_json.map((alternative, index) => (
                <button
                  key={index}
                  type="button"
                  className="w-full rounded-md border p-3 text-left text-sm hover:bg-muted/50"
                  onClick={() => setCaption(alternative)}
                >
                  {alternative}
                </button>
              ))}
            </div>
          ) : null}

          <div className="grid gap-2">
            <Label htmlFor="caption">Caption</Label>
            <Textarea
              id="caption"
              rows={5}
              value={caption}
              disabled={!isEditable}
              onChange={(event) => setCaption(event.target.value)}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-2">
              <Label htmlFor="cta">Call to action</Label>
              <Input
                id="cta"
                value={cta}
                disabled={!isEditable}
                onChange={(event) => setCta(event.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="hashtags">Hashtags</Label>
              <Input
                id="hashtags"
                value={hashtags}
                disabled={!isEditable}
                onChange={(event) => setHashtags(event.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => save.mutate()}
              disabled={!isEditable || save.isPending}
            >
              {save.isPending ? "Saving..." : "Save draft"}
            </Button>
            {canSubmit ? (
              <Button
                onClick={() => submit.mutate()}
                disabled={submit.isPending}
              >
                <Send className="mr-2 h-4 w-4" />
                Submit for approval
              </Button>
            ) : null}
            {canReview ? (
              <>
                <Button
                  onClick={() => approve.mutate()}
                  disabled={
                    approve.isPending || data.integrity_status === "failed"
                  }
                >
                  <CheckCircle2 className="mr-2 h-4 w-4" /> Approve
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    if (window.confirm("Reject this content draft?")) {
                      reject.mutate()
                    }
                  }}
                  disabled={reject.isPending}
                >
                  <XCircle className="mr-2 h-4 w-4" /> Reject
                </Button>
              </>
            ) : null}
          </div>
          {data.status === "approved" && data.approved_at ? (
            <p className="text-sm text-muted-foreground">
              Approved by Owner on {new Date(data.approved_at).toLocaleString()}
              .
            </p>
          ) : null}
        </CardContent>
      </Card>

      {["approved", "published", "publish_failed"].includes(data.status) ? (
        <Card>
          <CardHeader>
            <CardTitle>Instagram publishing</CardTitle>
            <CardDescription>
              Single-image feed post. Only the Owner can publish.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.status === "published" && publishJobs?.data[0] ? (
              <div className="space-y-1 text-sm">
                <p>Published successfully.</p>
                <a
                  href={publishJobs.data[0].remote_post_url ?? "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-primary underline"
                >
                  View post <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            ) : null}
            {publishJobs?.data[0]?.status === "failed" ? (
              <p className="text-sm text-destructive">
                {publishJobs.data[0].error_message ?? "Publishing failed"}
              </p>
            ) : null}
            <div className="flex flex-wrap gap-2">
              {isOwner && data.status === "approved" ? (
                <Button
                  onClick={() => publish.mutate()}
                  disabled={publish.isPending}
                >
                  <Share2 className="mr-2 h-4 w-4" />
                  {publish.isPending ? "Publishing..." : "Publish to Instagram"}
                </Button>
              ) : null}
              {isOwner && publishJobs?.data[0]?.status === "failed" ? (
                <Button
                  variant="outline"
                  onClick={() => retryPublish.mutate(publishJobs.data[0].id)}
                  disabled={retryPublish.isPending}
                >
                  <RefreshCw className="mr-2 h-4 w-4" /> Retry publish
                </Button>
              ) : null}
              {!isOwner ? (
                <p className="text-sm text-muted-foreground">
                  The brand Owner performs the final publish.
                </p>
              ) : null}
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
