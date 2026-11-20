export const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, code = 'request_failed', status = 0) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

export async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })
  const text = await response.text()
  let payload = null
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = null
    }
  }
  if (!response.ok || payload?.success === false) {
    throw new ApiError(
      payload?.error || `请求失败（HTTP ${response.status}）`,
      payload?.code || 'request_failed',
      response.status,
    )
  }
  return payload?.data ?? payload
}

export function fileUrl(jobId) {
  return `${API_BASE}/api/downloads/${encodeURIComponent(jobId)}/file`
}

export function apiUrl(path) {
  return `${API_BASE}${path}`
}
