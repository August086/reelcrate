import { apiFetch } from './client'

export function getConfig() {
  return apiFetch('/api/config')
}

export function parseVideo(url) {
  return apiFetch('/api/parse', {
    method: 'POST',
    body: JSON.stringify({ url }),
  })
}

export function createDownload(url, optionId) {
  return apiFetch('/api/downloads', {
    method: 'POST',
    body: JSON.stringify({ url, option_id: optionId, prefer: 'proxy' }),
  })
}

export function getDownload(jobId) {
  return apiFetch(`/api/downloads/${encodeURIComponent(jobId)}`)
}

export function getDirectUrl(url, optionId) {
  return apiFetch('/api/direct-url', {
    method: 'POST',
    body: JSON.stringify({ url, option_id: optionId }),
  })
}
