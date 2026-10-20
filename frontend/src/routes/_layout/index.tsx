import { createFileRoute, Link } from "@tanstack/react-router"
import { Users } from "lucide-react"

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

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({ meta: [{ title: "Dashboard - Jewelry Brand Studio" }] }),
})

function Dashboard() {
  const { user: currentUser } = useAuth()
  const { brand, brands } = useBrand()

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="max-w-2xl truncate text-2xl font-semibold">
            Hi, {currentUser?.full_name || currentUser?.email}
          </h1>
          <p className="text-muted-foreground">
            {brand
              ? `Working in ${brand.name}.`
              : "Create a brand workspace to get started."}
          </p>
        </div>
        {brand ? <CreateBrandDialog /> : null}
      </div>

      {!brand ? <NoBrand /> : null}

      {brand ? (
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Brand workspace</CardTitle>
              <CardDescription>
                {brand.name} · {brand.status}
              </CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              Your role:{" "}
              <span className="font-medium capitalize text-foreground">
                {brand.role.replace("_", " ")}
              </span>
              {brands.length > 1
                ? ` · ${brands.length} brands available`
                : " · one brand"}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Team</CardTitle>
              <CardDescription>
                Invite content managers or another owner.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" size="sm" asChild>
                <Link to="/team">
                  <Users className="mr-2 h-4 w-4" /> Manage team
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  )
}
