import { useMutation } from "@tanstack/react-query"
import { Plus } from "lucide-react"
import type { ReactNode } from "react"
import { useState } from "react"

import { BrandsService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useBrand } from "@/hooks/useBrand"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export function CreateBrandDialog({ trigger }: { trigger?: ReactNode }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const { refresh, selectBrand } = useBrand()

  const mutation = useMutation({
    mutationFn: async () => {
      const response = await BrandsService.createBrand({ body: { name } })
      return response.data
    },
    onSuccess: async (brand) => {
      await refresh()
      selectBrand(brand.id)
      showSuccessToast("Brand created")
      setName("")
      setOpen(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button size="sm">
            <Plus className="mr-1 h-4 w-4" /> New brand
          </Button>
        )}
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create brand</DialogTitle>
          <DialogDescription>
            Add a jewelry brand workspace. You become its owner.
          </DialogDescription>
        </DialogHeader>
        <form
          onSubmit={(event) => {
            event.preventDefault()
            if (name.trim()) mutation.mutate()
          }}
        >
          <div className="grid gap-2 py-2">
            <Label htmlFor="brand-name">Brand name</Label>
            <Input
              id="brand-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="e.g. Aurum Atelier"
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={!name.trim() || mutation.isPending}>
              {mutation.isPending ? "Creating..." : "Create brand"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
