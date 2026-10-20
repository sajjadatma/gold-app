import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft, CheckCircle2, RefreshCw, Upload } from "lucide-react"
import { useEffect, useState } from "react"

import { BrandModelsService, type ModelReferencePublic } from "@/client"
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
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { useBrand } from "@/hooks/useBrand"
import useCustomToast from "@/hooks/useCustomToast"
import { pageTitle, useI18n } from "@/i18n"
import { fetchPrivateFile } from "@/lib/privateFiles"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/models/$id")({
  component: ModelDetailPage,
  head: () => ({
    meta: [
      {
        title: pageTitle(
          "Brand Model - Jewelry Brand Studio",
          "مدل برند - استودیوی برند جواهرات",
        ),
      },
    ],
  }),
})

function ReferenceImage({
  brandId,
  modelId,
  reference,
  onCanonical,
  disabled = false,
}: {
  brandId: string
  modelId: string
  reference: ModelReferencePublic
  onCanonical: () => void
  disabled?: boolean
}) {
  const [url, setUrl] = useState<string | null>(null)
  const { t } = useI18n()

  useEffect(() => {
    let active = true
    let objectUrl: string | null = null
    fetchPrivateFile(
      `/api/v1/brands/${brandId}/models/${modelId}/references/${reference.id}/download`,
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
  }, [brandId, modelId, reference.id])

  return (
    <button
      type="button"
      onClick={onCanonical}
      disabled={disabled}
      className={`overflow-hidden rounded-lg border text-left transition-colors ${
        reference.is_canonical ? "border-primary ring-2 ring-primary/30" : ""
      }`}
    >
      <div className="aspect-[4/5] bg-muted">
        {url ? (
          <img
            src={url}
            alt={t("Model reference")}
            className="h-full w-full object-cover"
          />
        ) : (
          <Skeleton className="h-full w-full" />
        )}
      </div>
      <div className="flex items-center justify-between p-2 text-xs">
        <span>
          {reference.is_canonical ? t("Canonical") : t("Set canonical")}
        </span>
        {reference.is_canonical ? (
          <CheckCircle2 className="h-4 w-4 text-primary" />
        ) : null}
      </div>
    </button>
  )
}

function ModelDetailPage() {
  const { id } = Route.useParams()
  const { brand } = useBrand()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const { t, formatDate } = useI18n()
  const [file, setFile] = useState<File | null>(null)
  const [consentChecked, setConsentChecked] = useState(false)
  const [scope, setScope] = useState("brand_imagery")

  const { data, isLoading } = useQuery({
    queryKey: ["model", brand?.id, id],
    queryFn: async () =>
      (
        await BrandModelsService.readModel({
          path: { brand_id: brand?.id ?? "", model_id: id },
        })
      ).data,
    enabled: Boolean(brand),
  })

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["model", brand?.id, id] })
  }

  const previews = useMutation({
    mutationFn: async () =>
      BrandModelsService.generatePreviews({
        path: { brand_id: brand?.id ?? "", model_id: id },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast(t("Model previews generated"))
    },
    onError: handleError.bind(showErrorToast),
  })

  const upload = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error(t("Choose an image first"))
      return BrandModelsService.uploadReference({
        path: { brand_id: brand?.id ?? "", model_id: id },
        body: { file },
      })
    },
    onSuccess: async () => {
      setFile(null)
      await refresh()
      showSuccessToast(t("Reference uploaded"))
    },
    onError: handleError.bind(showErrorToast),
  })

  const canonical = useMutation({
    mutationFn: async (referenceId: string) =>
      BrandModelsService.setCanonicalReference({
        path: { brand_id: brand?.id ?? "", model_id: id },
        body: { reference_id: referenceId },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast(t("Canonical reference updated"))
    },
    onError: handleError.bind(showErrorToast),
  })

  const consent = useMutation({
    mutationFn: async () =>
      BrandModelsService.recordConsent({
        path: { brand_id: brand?.id ?? "", model_id: id },
        body: {
          confirmation_text_version: "mvp1-2026-01",
          permission_scope: scope,
        },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast(t("Consent recorded"))
    },
    onError: handleError.bind(showErrorToast),
  })

  const makeDefault = useMutation({
    mutationFn: async () =>
      BrandModelsService.setDefaultModel({
        path: { brand_id: brand?.id ?? "", model_id: id },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast(t("Default model updated"))
    },
    onError: handleError.bind(showErrorToast),
  })

  if (!brand) return <NoBrand />
  if (isLoading)
    return <p className="text-sm text-muted-foreground">{t("Loading...")}</p>
  if (!data)
    return (
      <p className="text-sm text-muted-foreground">{t("Model not found")}</p>
    )

  const configEntries = Object.entries(data.config_json).filter(
    ([, value]) => typeof value === "string" && value.trim(),
  )

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" asChild className="-ml-2">
        <Link to="/models">
          <ArrowLeft className="mr-2 h-4 w-4" /> {t("All models")}
        </Link>
      </Button>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{data.name}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Badge variant="outline">{t(data.type)}</Badge>
            <Badge
              variant={data.status === "ready" ? "default" : "secondary"}
              className="capitalize"
            >
              {t(data.status)}
            </Badge>
            {data.is_default ? <Badge>{t("Default")}</Badge> : null}
          </div>
        </div>
        <div className="flex gap-2">
          {data.type === "virtual" ? (
            <Button
              onClick={() => previews.mutate()}
              disabled={previews.isPending}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              {previews.isPending ? t("Generating...") : t("Generate previews")}
            </Button>
          ) : null}
          <Button
            variant="outline"
            onClick={() => makeDefault.mutate()}
            disabled={
              data.is_default ||
              data.status !== "ready" ||
              makeDefault.isPending
            }
          >
            {t("Set default")}
          </Button>
        </div>
      </div>

      {configEntries.length ? (
        <Card>
          <CardHeader>
            <CardTitle>{t("Visual direction")}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 text-sm sm:grid-cols-2">
            {configEntries.map(([key, value]) => (
              <div key={key}>
                <span className="capitalize text-muted-foreground">
                  {t(key.replace(/_/g, " "))}:{" "}
                </span>
                <span>{String(value)}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">{t("References")}</h2>
        {data.references.length === 0 ? (
          <p className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
            {t("No references yet.")}
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {data.references.map((reference) => (
              <ReferenceImage
                key={reference.id}
                brandId={brand.id}
                modelId={data.id}
                reference={reference}
                disabled={canonical.isPending}
                onCanonical={() => canonical.mutate(reference.id)}
              />
            ))}
          </div>
        )}
      </div>

      {data.type === "real" ? (
        <Card>
          <CardHeader>
            <CardTitle>{t("Real model references and consent")}</CardTitle>
            <CardDescription>
              {t(
                "Upload reference photos, then record the person's consent before this model can be used or made default.",
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="reference-file">{t("Reference photo")}</Label>
              <Input
                id="reference-file"
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
                {upload.isPending ? t("Uploading...") : t("Upload reference")}
              </Button>
            </div>

            {data.consent ? (
              <div className="rounded-md border border-emerald-500/40 bg-emerald-500/5 p-4 text-sm">
                <p className="font-medium">{t("Consent recorded")}</p>
                <p className="text-muted-foreground">
                  {t("Scope: {scope} · Version: {version} · {date}", {
                    scope: data.consent.permission_scope,
                    version: data.consent.confirmation_text_version,
                    date: formatDate(data.consent.confirmed_at, {
                      dateStyle: "medium",
                      timeStyle: "short",
                    }),
                  })}
                </p>
              </div>
            ) : (
              <div className="space-y-3 rounded-md border p-4">
                <div className="flex items-start gap-3">
                  <Checkbox
                    id="consent-check"
                    checked={consentChecked}
                    onCheckedChange={(checked) =>
                      setConsentChecked(checked === true)
                    }
                  />
                  <Label
                    htmlFor="consent-check"
                    className="font-normal leading-relaxed"
                  >
                    {t(
                      "I confirm that this person has consented to their likeness being used to create branded jewelry imagery for this brand.",
                    )}
                  </Label>
                </div>
                <div className="grid max-w-xs gap-2">
                  <Label htmlFor="consent-scope">{t("Permission scope")}</Label>
                  <Input
                    id="consent-scope"
                    value={scope}
                    onChange={(event) => setScope(event.target.value)}
                  />
                </div>
                <Button
                  onClick={() => consent.mutate()}
                  disabled={
                    !consentChecked || !scope.trim() || consent.isPending
                  }
                >
                  {t("Record consent")}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
