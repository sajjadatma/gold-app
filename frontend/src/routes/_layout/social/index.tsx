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
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/social/")({
  component: SocialPage,
  head: () => ({ meta: [{ title: "Social - Jewelry Brand Studio" }] }),
})

function SocialPage() {
  const { brand } = useBrand()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
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
      showSuccessToast("Instagram connection saved")
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
      showSuccessToast("Instagram disconnected")
    },
    onError: handleError.bind(showErrorToast),
  })

  if (!brand) return <NoBrand />
  if (isLoading)
    return (
      <p className="text-sm text-muted-foreground">Loading connection...</p>
    )

  const isOwner = brand.role === "owner"
  const connected = data?.status === "connected"

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Instagram</h1>
        <p className="text-sm text-muted-foreground">
          Connect a professional account to publish approved single-image feed
          posts.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Connection
            <Badge variant={connected ? "default" : "secondary"}>
              {data?.status ?? "disconnected"}
            </Badge>
          </CardTitle>
          <CardDescription>
            Tokens are stored server-side and never returned to the browser.
            Fake publishing is used unless the Graph provider is configured.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="account-id">Instagram account id</Label>
            <Input
              id="account-id"
              value={accountId}
              disabled={!isOwner}
              onChange={(event) => setAccountId(event.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="account-name">Account name</Label>
            <Input
              id="account-name"
              value={accountName}
              disabled={!isOwner}
              onChange={(event) => setAccountName(event.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="token">Access token</Label>
            <Input
              id="token"
              type="password"
              autoComplete="off"
              value={token}
              disabled={!isOwner}
              placeholder={
                connected ? "Leave blank to keep the current token" : ""
              }
              onChange={(event) => setToken(event.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              In fake mode a token is optional.
            </p>
          </div>

          {isOwner ? (
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => connect.mutate()}
                disabled={!accountId.trim() || connect.isPending}
              >
                <Link2 className="mr-2 h-4 w-4" />
                {connected ? "Update connection" : "Connect Instagram"}
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
                  <Unplug className="mr-2 h-4 w-4" /> Disconnect
                </Button>
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Only the brand Owner can change the social connection.
            </p>
          )}
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">
        MVP supports single-image feed posts only. Reels, stories, carousels,
        and scheduling are out of scope.
      </p>
    </div>
  )
}
