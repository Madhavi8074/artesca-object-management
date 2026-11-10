export function formatBytes(bytes: number): string {
  if (bytes <= 0) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

export function formatDate(dateString?: string | null): string {
  if (!dateString) return '-'
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return dateString
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dateString
  }
}

export function getFileBadgeClass(contentType?: string | null, filename?: string): string {
  const type = (contentType || '').toLowerCase()
  const name = (filename || '').toLowerCase()

  if (type.includes('pdf') || name.endsWith('.pdf')) return 'pdf'
  if (type.includes('image') || name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.svg'))
    return 'image'
  if (type.includes('json') || name.endsWith('.json')) return 'json'
  if (type.includes('text') || name.endsWith('.txt') || name.endsWith('.md')) return 'text'
  return 'default'
}
