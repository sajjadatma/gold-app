import { createFileRoute } from "@tanstack/react-router"

import ChangePassword from "@/components/UserSettings/ChangePassword"
import DeleteAccount from "@/components/UserSettings/DeleteAccount"
import UserInformation from "@/components/UserSettings/UserInformation"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useAuth from "@/hooks/useAuth"
import { pageTitle, useI18n } from "@/i18n"

const tabsConfig = (t: (key: string) => string) => [
  { value: "my-profile", title: t("My profile"), component: UserInformation },
  { value: "password", title: t("Password"), component: ChangePassword },
  { value: "danger-zone", title: t("Danger zone"), component: DeleteAccount },
]

export const Route = createFileRoute("/_layout/settings")({
  component: UserSettings,
  head: () => ({
    meta: [
      {
        title: pageTitle(
          "Settings - Jewelry Brand Studio",
          "تنظیمات - استودیوی برند جواهرات",
        ),
      },
    ],
  }),
})

function UserSettings() {
  const { user: currentUser } = useAuth()
  const { t } = useI18n()
  const tabs = tabsConfig(t)
  const finalTabs = currentUser?.is_superuser ? tabs.slice(0, 3) : tabs

  if (!currentUser) {
    return null
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {t("User Settings")}
        </h1>
        <p className="text-muted-foreground">
          {t("Manage your account settings and preferences")}
        </p>
      </div>

      <Tabs defaultValue="my-profile">
        <TabsList>
          {finalTabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.title}
            </TabsTrigger>
          ))}
        </TabsList>
        {finalTabs.map((tab) => (
          <TabsContent key={tab.value} value={tab.value}>
            <tab.component />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
