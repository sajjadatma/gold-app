import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { CheckCircle2, Save } from "lucide-react"
import { useEffect, useState } from "react"

import {
  type BrandAssetPublic,
  BrandImportService,
  BrandImportService as ImportService,
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
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useBrand } from "@/hooks/useBrand"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/brand/profile")({
  component: BrandProfilePage,
  head: () => ({ meta: [{ title: "Brand Profile - Jewelry Brand Studio" }] }),
})

type ColorEntry = {
  name?: string | null
  hex: string
  usage?: string | null
  provenance?: unknown
}
type TypographyEntry = {
  family: string
  role?: string | null
  provenance?: unknown
}
type LogoEntry = {
  asset_id?: string | null
  variant?: string | null
  provenance?: unknown
}
type ProfileData = {
  identity: {
    brand_name: string
    tagline: string
    story: string
    positioning: string
    audience: string[]
    personality: string[]
  }
  colors: ColorEntry[]
  typography: TypographyEntry[]
  logos: LogoEntry[]
  photography: {
    lighting: string[]
    backgrounds: string[]
    composition: string[]
    contrast: string
    shadow_style: string
    retouching: string[]
    prohibited_styles: string[]
  }
  tone_of_voice: {
    languages: string[]
    tone: string[]
    caption_style: string
    emoji_policy: string
    cta_style: string
    hashtag_style: string
  }
  human_model_style: {
    appearance: string[]
    makeup: string[]
    hair: string[]
    wardrobe: string[]
    hands_and_nails: string[]
    posing: string[]
  }
  graphic_system: {
    patterns: string[]
    decorative_elements: string[]
    layout_principles: string[]
  }
  social_media: {
    preferred_ratios: string[]
    visual_rules: string[]
    logo_rules: string[]
  }
  additional_sections: {
    title: string
    content: string[]
    page_number?: number | null
    confidence?: number
  }[]
  dos: string[]
  donts: string[]
  uncertainties: string[]
  [key: string]: unknown
}

function ListField({
  label,
  value,
  onChange,
  disabled,
}: {
  label: string
  value: string[]
  onChange: (value: string[]) => void
  disabled: boolean
}) {
  const [text, setText] = useState(value.join(", "))
  useEffect(() => setText(value.join(", ")), [value])
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      <Textarea
        value={text}
        disabled={disabled}
        rows={2}
        onChange={(event) => setText(event.target.value)}
        onBlur={() =>
          onChange(
            text
              .split(/[,\n]/)
              .map((item) => item.trim())
              .filter(Boolean),
          )
        }
      />
      <p className="text-xs text-muted-foreground">
        Separate values with commas.
      </p>
    </div>
  )
}

function BrandProfilePage() {
  const { brand } = useBrand()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [form, setForm] = useState<ProfileData | null>(null)

  const { data, isLoading, isError } = useQuery({
    queryKey: ["profile", brand?.id],
    queryFn: async () =>
      (
        await ImportService.readLatestProfile({
          path: { brand_id: brand?.id ?? "" },
        })
      ).data,
    enabled: Boolean(brand),
    retry: false,
  })

  const { data: assetData } = useQuery({
    queryKey: ["assets", brand?.id, "all"],
    queryFn: async () =>
      (
        await BrandImportService.readAssets({
          path: { brand_id: brand?.id ?? "" },
          query: {},
        })
      ).data,
    enabled: Boolean(brand),
  })

  useEffect(() => {
    if (data) {
      const profile = structuredClone(
        data.profile_json as unknown as ProfileData,
      )
      setForm({
        ...profile,
        human_model_style: profile.human_model_style ?? {
          appearance: [],
          makeup: [],
          hair: [],
          wardrobe: [],
          hands_and_nails: [],
          posing: [],
        },
        graphic_system: profile.graphic_system ?? {
          patterns: [],
          decorative_elements: [],
          layout_principles: [],
        },
        social_media: profile.social_media ?? {
          preferred_ratios: [],
          visual_rules: [],
          logo_rules: [],
        },
        additional_sections: profile.additional_sections ?? [],
      })
    }
  }, [data])

  const save = useMutation({
    mutationFn: async () => {
      if (!brand || !data || !form) throw new Error("Nothing to save")
      return (
        await ImportService.updateProfile({
          path: { brand_id: brand.id, profile_id: data.id },
          body: { profile_json: form as unknown as Record<string, unknown> },
        })
      ).data
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["profile", brand?.id] })
      showSuccessToast("Brand profile saved")
    },
    onError: handleError.bind(showErrorToast),
  })

  const activate = useMutation({
    mutationFn: async () => {
      if (!brand || !data) throw new Error("Nothing to activate")
      return (
        await ImportService.activateProfile({
          path: { brand_id: brand.id, profile_id: data.id },
        })
      ).data
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["profile", brand?.id] })
      showSuccessToast("Brand profile activated")
    },
    onError: handleError.bind(showErrorToast),
  })

  if (!brand) return <NoBrand />
  if (isLoading)
    return <p className="text-sm text-muted-foreground">Loading profile...</p>
  if (isError || !data || !form) {
    return (
      <div className="space-y-4 rounded-lg border border-dashed p-8">
        <h1 className="text-lg font-semibold">No brand profile yet</h1>
        <p className="text-sm text-muted-foreground">
          Import brand material and run brand intelligence first.
        </p>
        <Button asChild variant="outline">
          <Link to="/brand/import">Go to brand import</Link>
        </Button>
      </div>
    )
  }

  const isOwner = brand.role === "owner"
  const disabled = !isOwner
  const assets: BrandAssetPublic[] = assetData?.data ?? []
  const logoAssets = assets.filter((asset) =>
    ["logo", "graphic_element", "image", "design_source"].includes(
      asset.asset_type,
    ),
  )
  const selectedLogoIds = new Set(
    form.logos.map((logo) => logo.asset_id).filter(Boolean),
  )

  const patch = (updates: Partial<ProfileData>) =>
    setForm({ ...form, ...updates })

  return (
    <div className="space-y-6 pb-16">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Brand profile</h1>
          <p className="text-sm text-muted-foreground">
            Validate what was extracted from your existing brand material.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={data.status === "active" ? "default" : "secondary"}>
            v{data.version} · {data.status.replace("_", " ")}
          </Badge>
          {isOwner ? (
            <>
              <Button
                variant="outline"
                onClick={() => save.mutate()}
                disabled={save.isPending}
              >
                <Save className="mr-2 h-4 w-4" />
                {save.isPending ? "Saving..." : "Save changes"}
              </Button>
              <Button
                onClick={() => {
                  if (
                    window.confirm(
                      "Activate this profile? The previous active profile will be archived.",
                    )
                  ) {
                    activate.mutate()
                  }
                }}
                disabled={activate.isPending || data.status === "active"}
              >
                <CheckCircle2 className="mr-2 h-4 w-4" />
                {data.status === "active" ? "Active" : "Activate"}
              </Button>
            </>
          ) : (
            <Badge variant="outline">Owner can edit</Badge>
          )}
        </div>
      </div>

      {data.profile_json.uncertainties &&
      (data.profile_json.uncertainties as string[]).length ? (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/5 p-4">
          <p className="text-sm font-medium">Review these uncertainties</p>
          <ul className="mt-2 list-disc pl-5 text-sm text-muted-foreground">
            {(data.profile_json.uncertainties as string[]).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Identity</CardTitle>
          <CardDescription>
            Existing brand voice only. Do not invent a new identity.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="grid gap-2">
            <Label htmlFor="brand-name">Brand name</Label>
            <Input
              id="brand-name"
              value={form.identity.brand_name}
              disabled={disabled}
              onChange={(event) =>
                patch({
                  identity: {
                    ...form.identity,
                    brand_name: event.target.value,
                  },
                })
              }
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="tagline">Tagline</Label>
            <Input
              id="tagline"
              value={form.identity.tagline}
              disabled={disabled}
              onChange={(event) =>
                patch({
                  identity: { ...form.identity, tagline: event.target.value },
                })
              }
            />
          </div>
          <div className="grid gap-2 md:col-span-2">
            <Label htmlFor="story">Story</Label>
            <Textarea
              id="story"
              rows={3}
              value={form.identity.story}
              disabled={disabled}
              onChange={(event) =>
                patch({
                  identity: { ...form.identity, story: event.target.value },
                })
              }
            />
          </div>
          <div className="grid gap-2 md:col-span-2">
            <Label htmlFor="positioning">Positioning</Label>
            <Textarea
              id="positioning"
              rows={2}
              value={form.identity.positioning}
              disabled={disabled}
              onChange={(event) =>
                patch({
                  identity: {
                    ...form.identity,
                    positioning: event.target.value,
                  },
                })
              }
            />
          </div>
          <ListField
            label="Audience"
            value={form.identity.audience}
            disabled={disabled}
            onChange={(audience) =>
              patch({ identity: { ...form.identity, audience } })
            }
          />
          <ListField
            label="Personality"
            value={form.identity.personality}
            disabled={disabled}
            onChange={(personality) =>
              patch({ identity: { ...form.identity, personality } })
            }
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Colors</CardTitle>
          <CardDescription>
            Correct extracted values or add missing colors.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {form.colors.map((color, index) => (
            <div
              key={`${color.hex}-${index}`}
              className="flex flex-wrap items-end gap-2"
            >
              <Input
                aria-label="Color name"
                placeholder="Name"
                className="w-40"
                value={color.name ?? ""}
                disabled={disabled}
                onChange={(event) => {
                  const colors = [...form.colors]
                  colors[index] = { ...color, name: event.target.value }
                  patch({ colors })
                }}
              />
              <Input
                aria-label="Hex value"
                placeholder="#C9A227"
                className="w-32"
                value={color.hex}
                disabled={disabled}
                onChange={(event) => {
                  const colors = [...form.colors]
                  colors[index] = { ...color, hex: event.target.value }
                  patch({ colors })
                }}
              />
              <Input
                aria-label="Color usage"
                placeholder="Usage"
                className="w-48"
                value={color.usage ?? ""}
                disabled={disabled}
                onChange={(event) => {
                  const colors = [...form.colors]
                  colors[index] = { ...color, usage: event.target.value }
                  patch({ colors })
                }}
              />
              {isOwner ? (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    patch({ colors: form.colors.filter((_, i) => i !== index) })
                  }
                >
                  Remove
                </Button>
              ) : null}
            </div>
          ))}
          {isOwner ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                patch({
                  colors: [
                    ...form.colors,
                    { name: "", hex: "#000000", usage: "" },
                  ],
                })
              }
            >
              Add color
            </Button>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Typography</CardTitle>
          <CardDescription>Families and their roles.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {form.typography.map((font, index) => (
            <div
              key={`${font.family}-${index}`}
              className="flex flex-wrap items-end gap-2"
            >
              <Input
                aria-label="Font family"
                placeholder="Family"
                className="w-56"
                value={font.family}
                disabled={disabled}
                onChange={(event) => {
                  const typography = [...form.typography]
                  typography[index] = { ...font, family: event.target.value }
                  patch({ typography })
                }}
              />
              <Input
                aria-label="Font role"
                placeholder="Heading / body"
                className="w-44"
                value={font.role ?? ""}
                disabled={disabled}
                onChange={(event) => {
                  const typography = [...form.typography]
                  typography[index] = { ...font, role: event.target.value }
                  patch({ typography })
                }}
              />
              {isOwner ? (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    patch({
                      typography: form.typography.filter((_, i) => i !== index),
                    })
                  }
                >
                  Remove
                </Button>
              ) : null}
            </div>
          ))}
          {isOwner ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                patch({
                  typography: [...form.typography, { family: "", role: "" }],
                })
              }
            >
              Add typeface
            </Button>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Photography rules</CardTitle>
          <CardDescription>
            Guide image generation with existing visual rules.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <ListField
            label="Lighting"
            value={form.photography.lighting}
            disabled={disabled}
            onChange={(lighting) =>
              patch({ photography: { ...form.photography, lighting } })
            }
          />
          <ListField
            label="Backgrounds"
            value={form.photography.backgrounds}
            disabled={disabled}
            onChange={(backgrounds) =>
              patch({ photography: { ...form.photography, backgrounds } })
            }
          />
          <ListField
            label="Composition"
            value={form.photography.composition}
            disabled={disabled}
            onChange={(composition) =>
              patch({ photography: { ...form.photography, composition } })
            }
          />
          <ListField
            label="Prohibited styles"
            value={form.photography.prohibited_styles}
            disabled={disabled}
            onChange={(prohibited_styles) =>
              patch({ photography: { ...form.photography, prohibited_styles } })
            }
          />
          <div className="grid gap-2">
            <Label htmlFor="contrast">Contrast</Label>
            <Input
              id="contrast"
              value={form.photography.contrast}
              disabled={disabled}
              onChange={(event) =>
                patch({
                  photography: {
                    ...form.photography,
                    contrast: event.target.value,
                  },
                })
              }
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="shadow">Shadow style</Label>
            <Input
              id="shadow"
              value={form.photography.shadow_style}
              disabled={disabled}
              onChange={(event) =>
                patch({
                  photography: {
                    ...form.photography,
                    shadow_style: event.target.value,
                  },
                })
              }
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tone of voice</CardTitle>
          <CardDescription>
            Used for captions, CTAs, and hashtags.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <ListField
            label="Languages"
            value={form.tone_of_voice.languages}
            disabled={disabled}
            onChange={(languages) =>
              patch({ tone_of_voice: { ...form.tone_of_voice, languages } })
            }
          />
          <ListField
            label="Tone"
            value={form.tone_of_voice.tone}
            disabled={disabled}
            onChange={(tone) =>
              patch({ tone_of_voice: { ...form.tone_of_voice, tone } })
            }
          />
          {(
            [
              ["caption_style", "Caption style"],
              ["emoji_policy", "Emoji policy"],
              ["cta_style", "CTA style"],
              ["hashtag_style", "Hashtag style"],
            ] as const
          ).map(([key, label]) => (
            <div key={key} className="grid gap-2">
              <Label htmlFor={key}>{label}</Label>
              <Input
                id={key}
                value={form.tone_of_voice[key]}
                disabled={disabled}
                onChange={(event) =>
                  patch({
                    tone_of_voice: {
                      ...form.tone_of_voice,
                      [key]: event.target.value,
                    },
                  })
                }
              />
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Logos</CardTitle>
          <CardDescription>
            Choose the logo variants that belong to the active identity.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {logoAssets.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No logo candidates imported.
            </p>
          ) : (
            logoAssets.map((asset) => (
              <div
                key={asset.id}
                className="flex items-center gap-3 rounded-md border p-3 text-sm"
              >
                <Checkbox
                  aria-label={`Use ${asset.original_filename} as a logo`}
                  checked={selectedLogoIds.has(asset.id)}
                  disabled={disabled}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      patch({
                        logos: [
                          ...form.logos,
                          { asset_id: asset.id, variant: null },
                        ],
                      })
                    } else {
                      patch({
                        logos: form.logos.filter(
                          (logo) => logo.asset_id !== asset.id,
                        ),
                      })
                    }
                  }}
                />
                <span className="flex-1 truncate">
                  {asset.original_filename}
                </span>
                <Badge variant="outline">
                  {asset.asset_type.replace("_", " ")}
                </Badge>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Human model style</CardTitle>
          <CardDescription>
            How people wearing the jewelry should look and pose.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          {(
            [
              ["appearance", "Appearance"],
              ["makeup", "Makeup"],
              ["hair", "Hair"],
              ["wardrobe", "Wardrobe"],
              ["hands_and_nails", "Hands and nails"],
              ["posing", "Posing"],
            ] as const
          ).map(([key, label]) => (
            <ListField
              key={key}
              label={label}
              value={form.human_model_style[key]}
              disabled={disabled}
              onChange={(value) =>
                patch({
                  human_model_style: {
                    ...form.human_model_style,
                    [key]: value,
                  },
                })
              }
            />
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Graphic system</CardTitle>
          <CardDescription>
            Patterns and layout rules found in the brand book.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          {(
            [
              ["patterns", "Patterns"],
              ["decorative_elements", "Decorative elements"],
              ["layout_principles", "Layout principles"],
            ] as const
          ).map(([key, label]) => (
            <ListField
              key={key}
              label={label}
              value={form.graphic_system[key]}
              disabled={disabled}
              onChange={(value) =>
                patch({
                  graphic_system: { ...form.graphic_system, [key]: value },
                })
              }
            />
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Social media</CardTitle>
          <CardDescription>
            Ratios and visual rules for social posts.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          {(
            [
              ["preferred_ratios", "Preferred ratios"],
              ["visual_rules", "Visual rules"],
              ["logo_rules", "Logo rules"],
            ] as const
          ).map(([key, label]) => (
            <ListField
              key={key}
              label={label}
              value={form.social_media[key]}
              disabled={disabled}
              onChange={(value) =>
                patch({
                  social_media: { ...form.social_media, [key]: value },
                })
              }
            />
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Additional sections from the brand book</CardTitle>
          <CardDescription>
            Other topics found in the PDF (packaging, values, materials, care,
            partnerships, and more).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {form.additional_sections.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No additional sections were found.
            </p>
          ) : (
            form.additional_sections.map((section, index) => (
              <div
                key={`${section.title}-${index}`}
                className="space-y-2 rounded-md border p-3"
              >
                <div className="flex items-end gap-2">
                  <div className="grid flex-1 gap-2">
                    <Label htmlFor={`section-title-${index}`}>
                      Section title
                    </Label>
                    <Input
                      id={`section-title-${index}`}
                      value={section.title}
                      disabled={disabled}
                      onChange={(event) => {
                        const sections = [...form.additional_sections]
                        sections[index] = {
                          ...section,
                          title: event.target.value,
                        }
                        patch({ additional_sections: sections })
                      }}
                    />
                  </div>
                  {isOwner ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        patch({
                          additional_sections: form.additional_sections.filter(
                            (_, sectionIndex) => sectionIndex !== index,
                          ),
                        })
                      }
                    >
                      Remove
                    </Button>
                  ) : null}
                </div>
                <div className="grid gap-2">
                  <Label htmlFor={`section-content-${index}`}>Content</Label>
                  <Textarea
                    id={`section-content-${index}`}
                    rows={3}
                    value={section.content.join("\n")}
                    disabled={disabled}
                    onChange={(event) => {
                      const sections = [...form.additional_sections]
                      sections[index] = {
                        ...section,
                        content: event.target.value.split("\n"),
                      }
                      patch({ additional_sections: sections })
                    }}
                  />
                </div>
                {section.page_number ? (
                  <p className="text-xs text-muted-foreground">
                    Found on page {section.page_number}
                  </p>
                ) : null}
              </div>
            ))
          )}
          {isOwner ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                patch({
                  additional_sections: [
                    ...form.additional_sections,
                    { title: "New section", content: [""] },
                  ],
                })
              }
            >
              Add section
            </Button>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Dos &amp; don'ts</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <ListField
            label="Dos"
            value={form.dos}
            disabled={disabled}
            onChange={(dos) => patch({ dos })}
          />
          <ListField
            label="Don'ts"
            value={form.donts}
            disabled={disabled}
            onChange={(donts) => patch({ donts })}
          />
        </CardContent>
      </Card>

      {isOwner ? (
        <div className="fixed inset-x-0 bottom-0 border-t bg-background/95 p-3 backdrop-blur md:left-64">
          <div className="mx-auto flex max-w-7xl justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => save.mutate()}
              disabled={save.isPending}
            >
              Save changes
            </Button>
            <Button
              onClick={() => activate.mutate()}
              disabled={activate.isPending || data.status === "active"}
            >
              Activate profile
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
