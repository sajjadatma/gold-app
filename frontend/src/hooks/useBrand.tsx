import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useState,
} from "react"

import { type BrandPublic, BrandsService } from "@/client"

const STORAGE_KEY = "selected_brand_id"

type BrandContextValue = {
  brands: BrandPublic[]
  brand: BrandPublic | null
  isLoading: boolean
  selectBrand: (id: string) => void
  createBrand: (name: string) => Promise<BrandPublic>
  refresh: () => Promise<void>
}

const BrandContext = createContext<BrandContextValue | null>(null)

export function BrandProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ["brands"],
    queryFn: async () => (await BrandsService.readBrands()).data,
  })
  const brands = data?.data ?? []
  const [selectedId, setSelectedId] = useState<string | null>(() =>
    localStorage.getItem(STORAGE_KEY),
  )

  useEffect(() => {
    // Wait for the first fetch before deciding the selection is stale.
    if (isLoading) return
    if (!brands.length) {
      if (selectedId) {
        setSelectedId(null)
        localStorage.removeItem(STORAGE_KEY)
      }
      return
    }
    if (!selectedId || !brands.some((item) => item.id === selectedId)) {
      const next = brands[0].id
      setSelectedId(next)
      localStorage.setItem(STORAGE_KEY, next)
    }
  }, [brands, selectedId, isLoading])

  const brand = brands.find((item) => item.id === selectedId) ?? null

  const selectBrand = (id: string) => {
    setSelectedId(id)
    localStorage.setItem(STORAGE_KEY, id)
  }

  const createBrand = async (name: string) => {
    const created = (await BrandsService.createBrand({ body: { name } })).data
    // Put the new brand in the cache before selecting it so the provider
    // cannot fall back to the previously selected brand during a refetch.
    queryClient.setQueryData<{ data: BrandPublic[]; count: number }>(
      ["brands"],
      (old) => {
        if (!old) return { data: [created], count: 1 }
        return { data: [...old.data, created], count: old.count + 1 }
      },
    )
    selectBrand(created.id)
    await queryClient.invalidateQueries({ queryKey: ["brands"] })
    return created
  }

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["brands"] })
  }

  return (
    <BrandContext.Provider
      value={{ brands, brand, isLoading, selectBrand, createBrand, refresh }}
    >
      {children}
    </BrandContext.Provider>
  )
}

export function useBrand() {
  const context = useContext(BrandContext)
  if (!context) {
    throw new Error("useBrand must be used within BrandProvider")
  }
  return context
}
