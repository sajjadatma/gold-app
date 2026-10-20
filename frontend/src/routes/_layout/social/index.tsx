import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Link2, Unplug } from "lucide-react"
import { useEffect, useState } from "react"

import { PublishingService } from "@/client"
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
import { pageTitle, useI18n } from "@/i18n"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/social/")({
  component: SocialPage,
  head: () => ({
    meta: [
      {
        title: pageTitle(
          "Social - Jewelry Brand Studio",
          "شبکه اجتماعی - استودیوی برند جواهرات",
        ),
      },
    ],
  }),
})

function SocialPage() {
  const { brand } = useBrand()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const { t } = useI18n()
  const [accountId, setAccountId] = useState("")
  const [accountName, setAccountName] = useState("")
  const [token, setToken] = useState("")

  const { data, isLoading } = useQuery({
    queryKey: ["social", brand?.id],
    queryFn: async () =>
      (
        await PublishingService.readConnection({
          path: { brand_id: brand?.id ?? "" },
        })
      ).data,
    enabled: Boolean(brand),
  })

  useEffect(() => {
    if (data) {
      setAccountId(data.external_account_id ?? "")
      setAccountName(data.account_name ?? "")
    }
  }, [data])

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["social", brand?.id] })
  }

  const connect = useMutation({
    mutationFn: async () =>
      PublishingService.connectSocial({
        path: { brand_id: brand?.id ?? "" },
        body: {
          external_account_id: accountId,
          account_name: accountName,
          access_token: token || null,
        },
      }),
    onSuccess: async () => {
      setToken("")
      await refresh()
      showSuccessToast(t("Instagram connection saved"))
    },
    onError: handleError.bind(showErrorToast),
  })

  const disconnect = useMutation({
    mutationFn: async () =>
      PublishingService.disconnectSocial({
        path: { brand_id: brand?.id ?? "" },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast(t("Instagram disconnected"))
    },
    onError: handleError.bind(showErrorToast),
  })

  if (!brand) return <NoBrand />
  if (isLoading)
    return (
      <p className="text-sm text-muted-foreground">
        {t("Loading connection...")}
      </p>
    )

  const isOwner = brand.role === "owner"
  const connected = data?.status === "connected"

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{t("Instagram")}</h1>
        <p className="text-sm text-muted-foreground">
          {t(
            "Connect a professional account to publish approved single-image feed posts.",
          )}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {t("Connection")}
            <Badge variant={connected ? "default" : "secondary"}>
              {t(data?.status ?? "disconnected")}
            </Badge>
          </CardTitle>
          <CardDescription>
            {t(
              "Tokens are stored server-side and never returned to the browser. Fake publishing is used unless the Graph provider is configured.",
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="account-id">{t("Instagram account id")}</Label>
            <Input
              id="account-id"
              value={accountId}
              disabled={!isOwner}
              onChange={(event) => setAccountId(event.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="account-name">{t("Account name")}</Label>
            <Input
              id="account-name"
              value={accountName}
              disabled={!isOwner}
              onChange={(event) => setAccountName(event.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="token">{t("Access token")}</Label>
            <Input
              id="token"
              type="password"
              autoComplete="off"
              value={token}
              disabled={!isOwner}
              placeholder={
                connected ? t("Leave blank to keep the current token") : ""
              }
              onChange={(event) => setToken(event.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              {t("In fake mode a token is optional.")}
            </p>
          </div>

          {isOwner ? (
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => connect.mutate()}
                disabled={!accountId.trim() || connect.isPending}
              >
                <Link2 className="mr-2 h-4 w-4" />
                {connected ? t("Update connection") : t("Connect Instagram")}
              </Button>
              {connected ? (
                <Button
                  variant="outline"
                  onClick={() => {
                    if (
                      window.confirm("Disconnect Instagram for this brand?")
                    ) {
                      disconnect.mutate()
                    }
                  }}
                >
                  <Unplug className="mr-2 h-4 w-4" /> {t("Disconnect")}
                </Button>
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              {t("Only the brand Owner can change the social connection.")}
            </p>
          )}
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">
        {t(
          "MVP supports single-image feed posts only. Reels, stories, carousels, and scheduling are out of scope.",
        )}
      </p>
    </div>
  )
}
