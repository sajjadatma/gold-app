import {
  Camera,
  FileText,
  Gem,
  Home,
  Images,
  Palette,
  Share2,
  Upload,
  UserRound,
  Users,
} from "lucide-react"

import { BrandSwitcher } from "@/components/Brand/BrandSwitcher"
import { SidebarAppearance } from "@/components/Common/Appearance"
import { LanguageSwitcher } from "@/components/Common/LanguageSwitcher"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import { useI18n } from "@/i18n"
import { type Item, Main } from "./Main"
import { User } from "./User"

const baseItems = (t: (key: string) => string): Item[] => [
  { icon: Home, title: t("Dashboard"), path: "/" },
  { icon: Upload, title: t("Brand Import"), path: "/brand/import" },
  { icon: Images, title: t("Brand Assets"), path: "/brand/assets" },
  { icon: Palette, title: t("Brand Profile"), path: "/brand/profile" },
  { icon: UserRound, title: t("Models"), path: "/models" },
  { icon: Gem, title: t("Products"), path: "/products" },
  { icon: Camera, title: t("Studio"), path: "/studio" },
  { icon: FileText, title: t("Content"), path: "/content" },
  { icon: Share2, title: t("Social"), path: "/social" },
  { icon: Users, title: t("Team"), path: "/team" },
]

export function AppSidebar() {
  const { user: currentUser } = useAuth()
  const { t, dir } = useI18n()

  const items = currentUser?.is_superuser
    ? [...baseItems(t), { icon: Users, title: t("Admin"), path: "/admin" }]
    : baseItems(t)

  return (
    <Sidebar collapsible="icon" side={dir === "rtl" ? "right" : "left"}>
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <div className="pb-2">
        <BrandSwitcher />
      </div>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <LanguageSwitcher />
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
