import {
  Camera,
  FileText,
  Gem,
  Home,
  Images,
  Palette,
  Upload,
  UserRound,
  Users,
} from "lucide-react"

import { BrandSwitcher } from "@/components/Brand/BrandSwitcher"
import { SidebarAppearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import { type Item, Main } from "./Main"
import { User } from "./User"

const baseItems: Item[] = [
  { icon: Home, title: "Dashboard", path: "/" },
  { icon: Upload, title: "Brand Import", path: "/brand/import" },
  { icon: Images, title: "Brand Assets", path: "/brand/assets" },
  { icon: Palette, title: "Brand Profile", path: "/brand/profile" },
  { icon: UserRound, title: "Models", path: "/models" },
  { icon: Gem, title: "Products", path: "/products" },
  { icon: Camera, title: "Studio", path: "/studio" },
  { icon: FileText, title: "Content", path: "/content" },
  { icon: Users, title: "Team", path: "/team" },
]

export function AppSidebar() {
  const { user: currentUser } = useAuth()

  const items = currentUser?.is_superuser
    ? [...baseItems, { icon: Users, title: "Admin", path: "/admin" }]
    : baseItems

  return (
    <Sidebar collapsible="icon">
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
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
