import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Search } from "lucide-react"
import { Suspense } from "react"

import { ItemsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import AddItem from "@/components/Items/AddItem"
import { getColumns } from "@/components/Items/columns"
import PendingItems from "@/components/Pending/PendingItems"
import { pageTitle, useI18n } from "@/i18n"

function getItemsQueryOptions() {
  return {
    queryFn: async () =>
      (await ItemsService.readItems({ query: { skip: 0, limit: 100 } })).data,
    queryKey: ["items"],
  }
}

export const Route = createFileRoute("/_layout/items")({
  component: Items,
  head: () => ({
    meta: [
      {
        title: pageTitle(
          "Items - Jewelry Brand Studio",
          "آیتم‌ها - استودیوی برند جواهرات",
        ),
      },
    ],
  }),
})

function ItemsTableContent() {
  const { t } = useI18n()
  const { data: items } = useSuspenseQuery(getItemsQueryOptions())

  if (items.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Search className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">
          {t("You don't have any items yet")}
        </h3>
        <p className="text-muted-foreground">
          {t("Add a new item to get started")}
        </p>
      </div>
    )
  }

  return <DataTable columns={getColumns(t)} data={items.data} />
}

function ItemsTable() {
  return (
    <Suspense fallback={<PendingItems />}>
      <ItemsTableContent />
    </Suspense>
  )
}

function Items() {
  const { t } = useI18n()
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("Items")}</h1>
          <p className="text-muted-foreground">
            {t("Create and manage your items")}
          </p>
        </div>
        <AddItem />
      </div>
      <ItemsTable />
    </div>
  )
}
