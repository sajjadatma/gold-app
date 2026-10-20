import { createFileRoute, Link } from "@tanstack/react-router"
import { LogOut, Users } from "lucide-react"

import { CreateBrandDialog } from "@/components/Brand/CreateBrandDialog"
import { NoBrand } from "@/components/Common/NoBrand"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import useAuth from "@/hooks/useAuth"
import { useBrand } from "@/hooks/useBrand"
import { pageTitle, useI18n } from "@/i18n"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: pageTitle(
          "Dashboard - Jewelry Brand Studio",
          "داشبورد - استودیوی برند جواهرات",
        ),
      },
    ],
  }),
})

function Dashboard() {
  const { user: currentUser, logout } = useAuth()
  const { brand, brands } = useBrand()
  const { t } = useI18n()

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="max-w-2xl truncate text-2xl font-semibold">
            {t("Hi, {name}", {
              name: currentUser?.full_name || currentUser?.email || "",
            })}
          </h1>
          <p className="text-muted-foreground">
            {brand
              ? t("Working in {name}.", { name: brand.name })
              : t("Create a brand workspace to get started.")}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {brand ? <CreateBrandDialog /> : null}
          <Button variant="outline" onClick={logout}>
            <LogOut className="mr-2 h-4 w-4" />
            {t("Log out")}
          </Button>
        </div>
      </div>

      {!brand ? <NoBrand /> : null}

      {brand ? (
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>{t("Brand workspace")}</CardTitle>
              <CardDescription>
                {brand.name} · {t(brand.status)}
              </CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              {t("Your role:")}{" "}
              <span className="font-medium text-foreground">
                {t(brand.role)}
              </span>
              {brands.length > 1
                ? ` · ${t("{count} brands available", { count: brands.length })}`
                : ` · ${t("one brand")}`}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>{t("Team")}</CardTitle>
              <CardDescription>
                {t("Invite content managers or another owner.")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" size="sm" asChild>
                <Link to="/team">
                  <Users className="mr-2 h-4 w-4" /> {t("Manage team")}
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  )
}
