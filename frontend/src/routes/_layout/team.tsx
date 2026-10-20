import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Plus, Trash2 } from "lucide-react"
import { useState } from "react"

import {
  BrandsService,
  type MemberPublic,
  type MemberRole,
} from "@/client"
import { NoBrand } from "@/components/Common/NoBrand"
import { Badge } from "@/components/ui/badge"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useBrand } from "@/hooks/useBrand"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/team")({
  component: TeamPage,
  head: () => ({ meta: [{ title: "Team - Jewelry Brand Studio" }] }),
})

function AddMemberDialog({
  brandId,
  onAdded,
}: {
  brandId: string
  onAdded: () => Promise<void>
}) {
  const [open, setOpen] = useState(false)
  const [email, setEmail] = useState("")
  const [role, setRole] = useState<MemberRole>("content_manager")
  const { showErrorToast, showSuccessToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: async () =>
      (
        await BrandsService.addMember({
          path: { brand_id: brandId },
          body: { email, role },
        })
      ).data,
    onSuccess: async () => {
      await onAdded()
      showSuccessToast("Member added")
      setEmail("")
      setOpen(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="mr-1 h-4 w-4" /> Add member
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add team member</DialogTitle>
          <DialogDescription>
            The person must already have an account in this application.
          </DialogDescription>
        </DialogHeader>
        <form
          onSubmit={(event) => {
            event.preventDefault()
            if (email.trim()) mutation.mutate()
          }}
        >
          <div className="grid gap-3 py-2">
            <div className="grid gap-2">
              <Label htmlFor="member-email">Email</Label>
              <Input
                id="member-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="name@brand.com"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="member-role">Role</Label>
              <Select
                value={role}
                onValueChange={(value) => setRole(value as MemberRole)}
              >
                <SelectTrigger id="member-role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="content_manager">
                    Content Manager
                  </SelectItem>
                  <SelectItem value="owner">Owner</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Adding..." : "Add member"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function TeamPage() {
  const { brand } = useBrand()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()

  const { data, isLoading } = useQuery({
    queryKey: ["members", brand?.id],
    queryFn: async () =>
      (
        await BrandsService.readMembers({
          path: { brand_id: brand?.id ?? "" },
        })
      ).data,
    enabled: Boolean(brand),
  })

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["members", brand?.id] })
  }

  const updateMutation = useMutation({
    mutationFn: async ({
      membershipId,
      role,
    }: {
      membershipId: string
      role: MemberRole
    }) =>
      BrandsService.updateMember({
        path: { brand_id: brand?.id ?? "", membership_id: membershipId },
        body: { role },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast("Role updated")
    },
    onError: handleError.bind(showErrorToast),
  })

  const removeMutation = useMutation({
    mutationFn: async (membershipId: string) =>
      BrandsService.deleteMember({
        path: { brand_id: brand?.id ?? "", membership_id: membershipId },
      }),
    onSuccess: async () => {
      await refresh()
      showSuccessToast("Member removed")
    },
    onError: handleError.bind(showErrorToast),
  })

  if (!brand) return <NoBrand />

  const isOwner = brand.role === "owner"
  const members: MemberPublic[] = data?.data ?? []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Team</h1>
          <p className="text-sm text-muted-foreground">
            People with access to {brand.name}.
          </p>
        </div>
        {isOwner ? <AddMemberDialog brandId={brand.id} onAdded={refresh} /> : null}
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading members...</p>
      ) : (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                {isOwner ? <TableHead className="w-16" /> : null}
              </TableRow>
            </TableHeader>
            <TableBody>
              {members.map((member) => (
                <TableRow key={member.id}>
                  <TableCell>{member.full_name || "—"}</TableCell>
                  <TableCell>{member.email}</TableCell>
                  <TableCell>
                    {isOwner ? (
                      <Select
                        value={member.role}
                        onValueChange={(value) =>
                          updateMutation.mutate({
                            membershipId: member.id,
                            role: value as MemberRole,
                          })
                        }
                      >
                        <SelectTrigger className="w-44" aria-label="Member role">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="owner">Owner</SelectItem>
                          <SelectItem value="content_manager">
                            Content Manager
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    ) : (
                      <Badge variant="outline" className="capitalize">
                        {member.role.replace("_", " ")}
                      </Badge>
                    )}
                  </TableCell>
                  {isOwner ? (
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`Remove ${member.email}`}
                        onClick={() => {
                          if (
                            window.confirm(
                              `Remove ${member.email} from ${brand.name}?`,
                            )
                          ) {
                            removeMutation.mutate(member.id)
                          }
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  ) : null}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
