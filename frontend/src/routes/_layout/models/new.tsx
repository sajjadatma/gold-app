import { useMutation } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"

import { BrandModelsService } from "@/client"
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

export const Route = createFileRoute("/_layout/models/new")({
  component: NewModelPage,
  head: () => ({
    meta: [
      {
        title: pageTitle(
          "New Brand Model - Jewelry Brand Studio",
          "مدل جدید برند - استودیوی برند جواهرات",
        ),
      },
    ],
  }),
})

function NewModelPage() {
  const { brand } = useBrand()
  const navigate = useNavigate()
  const { showErrorToast } = useCustomToast()
  const { t } = useI18n()
  const [type, setType] = useState<"virtual" | "real">("virtual")
  const [name, setName] = useState("")
  const [config, setConfig] = useState({
    gender_presentation: "",
    age_range: "",
    skin: "",
    hair: "",
    makeup: "",
    wardrobe: "",
    hands_and_nails: "",
    notes: "",
  })

  const mutation = useMutation({
    mutationFn: async () => {
      if (!brand) throw new Error(t("No brand selected"))
      return (
        await BrandModelsService.createModel({
          path: { brand_id: brand.id },
          body: { type, name, config_json: config },
        })
      ).data
    },
    onSuccess: (model) => {
      navigate({ to: "/models/$id", params: { id: model.id } })
    },
    onError: handleError.bind(showErrorToast),
  })

  if (!brand) return <NoBrand />

  const field = (key: keyof typeof config, label: string) => (
    <div className="grid gap-2">
      <Label htmlFor={key}>{label}</Label>
      <Input
        id={key}
        value={config[key]}
        onChange={(event) =>
          setConfig({ ...config, [key]: event.target.value })
        }
      />
    </div>
  )

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{t("New brand model")}</h1>
        <p className="text-sm text-muted-foreground">
          {t(
            "Virtual models use reference-based generation. Real models require reference photos and a consent record.",
          )}
        </p>
      </div>

      <form
        onSubmit={(event) => {
          event.preventDefault()
          if (name.trim()) mutation.mutate()
        }}
      >
        <Card>
          <CardHeader>
            <CardTitle>{t("Model basics")}</CardTitle>
            <CardDescription>
              {t("The active brand profile guides the style.")}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="model-type">{t("Type")}</Label>
              <Select
                value={type}
                onValueChange={(value) => setType(value as "virtual" | "real")}
              >
                <SelectTrigger id="model-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="virtual">{t("Virtual model")}</SelectItem>
                  <SelectItem value="real">{t("Real model")}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="model-name">{t("Name")}</Label>
              <Input
                id="model-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder={t("e.g. Aria")}
              />
            </div>

            {type === "virtual" ? (
              <div className="grid gap-4 md:grid-cols-2">
                {field("gender_presentation", t("Gender presentation"))}
                {field("age_range", t("Apparent age range"))}
                {field("skin", t("Skin appearance"))}
                {field("hair", t("Hair"))}
                {field("makeup", t("Makeup"))}
                {field("wardrobe", t("Wardrobe"))}
                {field("hands_and_nails", t("Hands and nails"))}
                <div className="grid gap-2 md:col-span-2">
                  <Label htmlFor="notes">{t("Notes")}</Label>
                  <Textarea
                    id="notes"
                    rows={3}
                    value={config.notes}
                    onChange={(event) =>
                      setConfig({ ...config, notes: event.target.value })
                    }
                  />
                </div>
              </div>
            ) : (
              <p className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
                {t(
                  "Create the model first, then upload reference photos and record the model's consent on the detail page.",
                )}
              </p>
            )}

            <Button type="submit" disabled={!name.trim() || mutation.isPending}>
              {mutation.isPending ? t("Creating...") : t("Create model")}
            </Button>
          </CardContent>
        </Card>
      </form>
    </div>
  )
}
