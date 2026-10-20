const baseUrl = import.meta.env.VITE_API_URL ?? ""

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("access_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function fetchPrivateFile(path: string): Promise<Blob> {
  const response = await fetch(`${baseUrl}${path}`, { headers: authHeaders() })
  if (!response.ok) {
    throw new Error("Unable to load file")
  }
  return response.blob()
}

export async function downloadPrivateFile(path: string, filename: string) {
  const blob = await fetchPrivateFile(path)
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export async function uploadBrandFiles(
  brandId: string,
  files: File[],
): Promise<unknown> {
  const formData = new FormData()
  for (const file of files) {
    formData.append("files", file)
  }
  const response = await fetch(`${baseUrl}/api/v1/brands/${brandId}/imports`, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  })
  if (!response.ok) {
    let detail = "Upload failed"
    try {
      const body = await response.json()
      detail = body.detail ?? detail
    } catch {
      // keep the generic message
    }
    throw new Error(detail)
  }
  return response.json()
}
