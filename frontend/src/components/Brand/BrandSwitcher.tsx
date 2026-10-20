import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useBrand } from "@/hooks/useBrand"

export function BrandSwitcher() {
  const { brands, brand, selectBrand } = useBrand()

  if (!brands.length) {
    return (
      <p className="px-2 text-xs text-muted-foreground">No brand selected</p>
    )
  }

  return (
    <div className="flex items-center gap-2 px-1">
      <Select value={brand?.id} onValueChange={selectBrand}>
        <SelectTrigger
          aria-label="Select brand"
          className="h-9 flex-1 group-data-[collapsible=icon]:hidden"
        >
          <SelectValue placeholder="Select brand" />
        </SelectTrigger>
        <SelectContent>
          {brands.map((item) => (
            <SelectItem key={item.id} value={item.id}>
              {item.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {brand ? (
        <Badge
          variant="outline"
          className="capitalize group-data-[collapsible=icon]:hidden"
        >
          {brand.role.replace("_", " ")}
        </Badge>
      ) : null}
    </div>
  )
}
